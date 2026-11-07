from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import logging
import secrets
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from uuid import UUID

from src.models.basic_authentication_shemas import MatchAuthentication, UserTable
from src.models.basic_authentication_models import UserModel
from src.models.dc_models import MatchNameModel
from src.load_secrets import pepper_data

logging.basicConfig(level=logging.INFO)


class CreateAuthentication:
    @staticmethod
    async def create_user_data(username: str, password: str, session: AsyncSession) -> None:
        """Create a user, or replace the password of an existing one

        Args:
            username (str): username of the user
            password (str): plain text password, stored only as a salted hash
            session (AsyncSession): session to connect to the database
        """
        salt = secrets.token_hex(8)
        hash_password = hashlib.sha256((password + salt + pepper_data).encode()).hexdigest()

        # An upsert, so that replicas starting together can seed the same users.
        stmt = insert(UserTable).values(
            username=username, hash_password=hash_password, salt=salt
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[UserTable.username],
            set_={"hash_password": hash_password, "salt": salt},
        )
        try:
            await session.execute(stmt)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def create_match_data(
        user_data: UserModel, match_id: UUID, match_team_name: str, session: AsyncSession
    ) -> None:
        """Create match data to authenticate the user

        Args:
            user_data (UserModel): username and password to authenticate the user
            match_id (UUID): To identify the match
            match_team_name (str): team0 or team1
            session (AsyncSession): session to connect to the database
        """        
        try:
            match_auth = MatchAuthentication(
                username=user_data.username,
                hash_password=user_data.hash_password,
                match_team_name=match_team_name,
                match_id=match_id,
                created_at=datetime.now(),
                expired_at=datetime.now() + timedelta(days=14),
            )
            session.add(match_auth)
            await session.commit()

        except Exception as e:
            await session.rollback()
            logging.error(f"Error creating match data: {e}")


class ReadAuthentication:
    @staticmethod
    async def read_user_data(username: str, session: AsyncSession) -> UserModel:
        """Read user data to get salt and password hash

        Args:
            username (str): username of the user
            session (AsyncSession): session to connect to the database

        Returns:
            UserModel: username, password and salt
        """
        stmt = select(UserTable).where(UserTable.username == username)
        result = await session.execute(stmt)
        result = result.scalars().first()
        if result is None:
            logging.error("User not found")
            return None
        user = UserModel(
            username=result.username,
            hash_password=result.hash_password,
            salt=result.salt,
        )
        return user

    @staticmethod
    async def read_match_data(user_data: UserModel, match_id: UUID, session: AsyncSession) -> str:
        """Read match data to get match team name("team0" or "team1")

        Args:
            user_data (UserModel): username and password to authenticate the user
            match_id (UUID): To identify the match
            session (AsyncSession): session to connect to the database

        Returns:
            MatchAuthenticationModel: match team name and match id
        """
        stmt = select(MatchAuthentication).where(
            MatchAuthentication.username == user_data.username,
            MatchAuthentication.match_id == match_id,
        )
        result = await session.execute(stmt)
        result = result.scalars().first()
        if result is None:
            logging.error("Match data not found")
            return None
        match_team_name = result.match_team_name
        return match_team_name


class DeleteAuthentication:
    @staticmethod
    async def delete_match_data(username: str, match_id: UUID, session: AsyncSession) -> None:
        """Delete match data for the user

        Args:
            username (str): username of the user
            match_id (UUID): match id to delete
            session (AsyncSession): session to connect to the database
        """
        try:
            stmt = select(MatchAuthentication).where(
                MatchAuthentication.username == username,
                MatchAuthentication.match_id == match_id,
            )
            result = await session.execute(stmt)
            result = result.scalars().first()
            if result is None:
                logging.error("Match data not found")
                return None
            await session.delete(result)
            await session.commit()

        except Exception as e:
            logging.error(f"Error deleting match data: {e}")

    @staticmethod
    async def delete_expired_match_data(session: AsyncSession):
        """Delete expired match data
        
        Args:
            session (AsyncSession): session to connect to the database
        """

        try:
            # A single DELETE, so replicas running this job together can't conflict.
            await session.execute(
                delete(MatchAuthentication).where(
                    MatchAuthentication.expired_at < datetime.now()
                )
            )
            await session.commit()

        except Exception as e:
            await session.rollback()
            logging.error(f"Error deleting expired match data: {e}")
