import logging
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import func
from app.configuration.db import ConnectionManager
from app.models.models import RoleEntity
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.pydantic_models import RoleDTO, StatusConstant
from app.generated_app.models import CreateRole, ResponseBO, PageableResponse

class RoleService:

    @staticmethod
    async def check_role_exists(role_name: str, logger: logging.Logger):
        async with ConnectionManager() as session:
            try:
                # Query to check if a role with the same name exists
                existing_role = await session.execute(
                    select(RoleEntity).where(RoleEntity.name == role_name)
                )
                role = existing_role.scalar()

                if role:  # If a role is found, return conflict
                    logger.warning(f"Role with name '{role_name}' already exists.")
                    return True  # Conflict found

                return False  # No conflict, role_name does not exist

            except SQLAlchemyError as e:
                logger.error(f"Error while checking role existence: {e}")
                raise HTTPException(status_code=500, detail="An error occurred while checking role existence.")

    @staticmethod
    async def role_exists(session: AsyncSession, name: str, current_role_id: int) -> bool:
        """Check if the role exists in the database other than the given role ID."""
        stmt = select(RoleEntity).where(RoleEntity.name == name).where(RoleEntity.id != current_role_id)
        result = await session.execute(stmt)
        return result.scalars().first() is not None

    @staticmethod
    async def fetch_role_by_id(role_id: int, session, logger: logging.Logger) -> RoleEntity:
        """Fetch a role by its ID."""
        try:
            logger.info(f"Fetching role with ID: {role_id}")
            role = await session.get(RoleEntity, role_id)

            if role:
                logger.info(f"Role found: {role_id}")
            else:
                logger.warning(f"Role with ID {role_id} not found.")

            return role
        except SQLAlchemyError as e:
            logger.error(f"Error fetching role with ID {role_id}: {e}")
            raise Exception(f"Error fetching role with ID {role_id}: {e}")

    async def create_role(self, body: CreateRole, logger: logging.Logger) -> ResponseBO:
        try:
            logger.info(f"Received request with data: {body}")

            async with ConnectionManager() as session:
                # Check if the role already exists in the database
                conflict = await self.check_role_exists(body.name, logger)
                if conflict:
                    logger.error(f"Role '{body.name}' already exists.")
                    return ResponseBO(
                        code=409,
                        status="FAILURE",
                        data=None,
                        message=f"Role '{body.name}" + " " + StatusConstant.EXISTS,
                    )

                # Proceed with role creation if no conflict
                new_role = self.dto_to_entity(body, logger)

                session.add(new_role)
                await session.commit()
                await session.refresh(new_role)
                logger.info(f"Role created: {new_role}")

                return ResponseBO(
                    code=201,
                    status="SUCCESS",
                    data=self.entity_to_dto(new_role, logger),
                    message=StatusConstant.CREATED

                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to create role: {e}")
            await session.rollback()
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR,
            )

        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            return ResponseBO(
                code=400,
                status="FAILURE",
                data=None,
                message=StatusConstant.BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR,
            )

    async def update_role(self, role_id: int, body: CreateRole, logger: logging.Logger) -> ResponseBO:
        try:
            logger.info(f"Received request to update role with ID {role_id} and data: {body}")

            async with ConnectionManager() as session:
                # Check for conflict if the role name already exists
                if await self.role_exists(session, body.name, role_id):
                    logger.error(f"Conflict: Role '{body.name}' already exists.")
                    return ResponseBO(
                        code=409,
                        status="FAILURE",
                        data=None,
                        message=f"Role '{body.name}'" + " " + StatusConstant.EXISTS,
                    )

                # Fetch the existing role
                existing_role = await self.fetch_role_by_id(role_id, session, logger)
                if not existing_role:
                    logger.error(f"Role with ID {role_id} not found.")
                    return ResponseBO(
                        code=404,
                        status="FAILURE",
                        data=None,
                        message="Role" + " " + StatusConstant.NOT_FOUND
                    )

                # Update the role's fields with the new data
                for key, value in body.dict(exclude_unset=True).items():
                    setattr(existing_role, key, value)

                await session.commit()
                await session.refresh(existing_role)
                logger.info(f"Role updated: {existing_role}")

                return ResponseBO(
                    code=200,
                    status="SUCCESS",
                    message=StatusConstant.UPDATED,
                    data=self.entity_to_dto(existing_role, logger)
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to update role: {e}")
            await session.rollback()
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR,
            )

        except ValueError as ve:
            logger.error(f"ValueError occurred: {ve}")
            return ResponseBO(
                code=400,
                status="FAILURE",
                data=None,
                message=StatusConstant.BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return ResponseBO(
                code=500,
                status="FAILURE",
                embedded=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR,
            )

    async def get_role_by_id(self, role_id: int,logger:logging.Logger) -> ResponseBO:
        try:
            logger.info(f"Received request to get role with ID {role_id}")

            async with ConnectionManager() as session:
                # Fetch the role by ID from the database
                role = await self.fetch_role_by_id(role_id, session, logger)

                if not role:
                    logger.error(f"Role with ID {role_id} not found.")
                    return ResponseBO(
                        code=404,
                        status="FAILURE",
                        data=None,
                        message="Role"+" "+StatusConstant.NOT_FOUND
                    )

                # Convert entity to DTO and return response
                logger.info(f"Role found: {role}")
                return ResponseBO(
                    code=200,  # OK status code
                    status="SUCCESS",
                    message=StatusConstant.GET,
                    data=self.entity_to_dto(role, logger)
                )

        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while retrieving role: {e}")
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR,
            )

    async def get_all_roles(self, logger: logging.Logger, page: int = 1, size: int = 10,
                            search_key: Optional[str] = None) -> PageableResponse:
        try:
            logger.info("Received request to get all roles with pagination and search filter")

            async with ConnectionManager() as session:
                query = select(RoleEntity)

                if search_key:
                    query = query.filter(RoleEntity.name.ilike(f"%{search_key}%"))

                offset = (page - 1) * size
                query = query.offset(offset).limit(size)

                roles = await session.execute(query)
                roles_list = roles.scalars().all()

                if not roles_list:
                    logger.info("No roles found matching the criteria.")
                    return PageableResponse(
                        code=204,
                        status="SUCCESS",
                        message=StatusConstant.NO_CONTENT,
                        page=page,
                        size=size,
                        totalPages=0,
                        totalElements=0,
                        data=[]
                    )

                logger.info(f"Total roles found: {len(roles_list)}")

                roles_dto_list = [self.entity_to_dto(role, logger) for role in roles_list]

                total_elements = await session.execute(select(func.count()).select_from(query))
                total_elements = total_elements.scalar()

                total_pages = (total_elements // size) + (1 if total_elements % size > 0 else 0)

                return PageableResponse(
                    code=200,
                    status="SUCCESS",
                    page=page,
                    size=size,
                    message=StatusConstant.GET_LIST,
                    totalPages=total_pages,
                    totalElements=total_elements,
                    data=roles_dto_list
                )


        except SQLAlchemyError as e:
            logger.error(f"Database error occurred while retrieving roles: {e}")
            return PageableResponse(
                code=500,
                status="FAILURE",
                message=StatusConstant.INTERNAL_SERVER_ERROR,
                page=page,
                size=size,
                data=None,
                totalPages=0,
                totalElements=0
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return PageableResponse(
                code=500,
                status="FAILURE",
                message=StatusConstant.INTERNAL_SERVER_ERROR,
                page=page,
                size=size,
                data=None,
                totalPages=0,
                totalElements=0
            )

    async def delete_role(self, role_id: int, logger:logging.Logger) -> ResponseBO:
        logger.info(f"Received request to delete role with ID {role_id}")

        try:

            async with ConnectionManager() as session:
                # Fetch the role using a separate function
                role = await self.fetch_role_by_id(role_id, session, logger)
                if not role:
                    logger.error(f"Role with ID {role_id} not found.")
                    return ResponseBO(
                        code=404,
                        status="FAILURE",
                        data=None,
                        message="Role"+" "+StatusConstant.NOT_FOUND
                    )

                # Proceed with deletion
                await session.delete(role)  # Delete the role
                await session.commit()  # Commit the changes
                logger.info(f"Role deleted: {role_id}")

                return ResponseBO(
                    code=200,
                    status="SUCCESS",
                    message=StatusConstant.DELETED,
                    data=None  # No additional data needed for delete response
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to delete role: {e}")
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return ResponseBO(
                code=500,
                status="FAILURE",
                data=None,
                message=StatusConstant.INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def entity_to_dto(role_entity: RoleEntity, logger) -> RoleDTO:
        logger.debug(f"Converting RoleEntity to RoleDTO: {role_entity}")
        dto = RoleDTO(
            id=role_entity.id,
            name=role_entity.name,
            description=role_entity.description
        )
        logger.info(f"Converted RoleEntity to RoleDTO: {dto}")
        return dto

    @staticmethod
    def dto_to_entity(role_dto: CreateRole, logger) -> RoleEntity:
        logger.debug(f"Converting CreateRole DTO to RoleEntity: {role_dto}")
        entity = RoleEntity(
            name=role_dto.name,
            description=role_dto.description
        )
        logger.info(f"Converted CreateRole DTO to RoleEntity: {entity}")
        return entity