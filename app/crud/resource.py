# app/crud/resource.py
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.models.resource import Resource, ResourceCategory
from app.schemas.resource import ResourceCreate, ResourceUpdate


def get_resource(db: Session, resource_id: int) -> Optional[Resource]:
    return db.query(Resource).filter(Resource.id == resource_id).first()


def get_resources(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    title: Optional[str] = None,
    description: Optional[str] = None,
    subject: Optional[str] = None,
    category_id: Optional[int] = None,
    file_format: Optional[str] = None,
    is_featured: Optional[bool] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> List[Resource]:
    query = db.query(Resource)
    if title:
        query = query.filter(Resource.title.ilike(f"%{title}%"))
    if description:
        query = query.filter(Resource.description.ilike(f"%{description}%"))
    if subject:
        query = query.filter(Resource.subject.ilike(f"%{subject}%"))
    if category_id is not None:
        query = query.filter(Resource.category_id == category_id)
    if file_format:
        query = query.filter(Resource.file_format == file_format.lower())
    if is_featured is not None:
        query = query.filter(Resource.is_featured == is_featured)
    if created_after:
        query = query.filter(Resource.created_at >= created_after)
    if created_before:
        query = query.filter(Resource.created_at <= created_before)
    return query.offset(skip).limit(limit).all()


def count_resources(
    db: Session,
    title: Optional[str] = None,
    description: Optional[str] = None,
    subject: Optional[str] = None,
    category_id: Optional[int] = None,
    file_format: Optional[str] = None,
    is_featured: Optional[bool] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> int:
    query = db.query(Resource)
    if title:
        query = query.filter(Resource.title.ilike(f"%{title}%"))
    if description:
        query = query.filter(Resource.description.ilike(f"%{description}%"))
    if subject:
        query = query.filter(Resource.subject.ilike(f"%{subject}%"))
    if category_id is not None:
        query = query.filter(Resource.category_id == category_id)
    if file_format:
        query = query.filter(Resource.file_format == file_format.lower())
    if is_featured is not None:
        query = query.filter(Resource.is_featured == is_featured)
    if created_after:
        query = query.filter(Resource.created_at >= created_after)
    if created_before:
        query = query.filter(Resource.created_at <= created_before)
    return query.count()


def create_resource(db: Session, resource: ResourceCreate, file_path: str) -> Resource:
    db_resource = Resource(
        title=resource.title,
        description=resource.description,
        subject=resource.subject,
        category_id=resource.category_id,
        file_path=file_path,
        file_format=resource.file_format,
        is_featured=resource.is_featured,
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


def update_resource(db: Session, resource_id: int, resource_update: ResourceUpdate) -> Optional[Resource]:
    db_resource = get_resource(db, resource_id)
    if not db_resource:
        return None
    for key, value in resource_update.model_dump(exclude_unset=True).items():
        setattr(db_resource, key, value)
    db.commit()
    db.refresh(db_resource)
    return db_resource


def delete_resource(db: Session, resource_id: int) -> bool:
    db_resource = get_resource(db, resource_id)
    if not db_resource:
        return False
    if os.path.exists(db_resource.file_path):
        os.remove(db_resource.file_path)
    db.delete(db_resource)
    db.commit()
    return True


def increment_view_count(db: Session, resource_id: int) -> Optional[Resource]:
    db_resource = get_resource(db, resource_id)
    if db_resource:
        db_resource.view_count += 1
        db.commit()
        db.refresh(db_resource)
    return db_resource


def get_categories(db: Session) -> List[ResourceCategory]:
    return db.query(ResourceCategory).all()


def search_resources(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 10,
    category_id: Optional[int] = None,
    file_format: Optional[str] = None,
    is_featured: Optional[bool] = None,
) -> List[Resource]:
    search_filter = or_(
        Resource.title.ilike(f"%{query}%"),
        Resource.description.ilike(f"%{query}%"),
        Resource.subject.ilike(f"%{query}%"),
    )
    q = db.query(Resource).filter(search_filter)
    if category_id is not None:
        q = q.filter(Resource.category_id == category_id)
    if file_format:
        q = q.filter(Resource.file_format == file_format.lower())
    if is_featured is not None:
        q = q.filter(Resource.is_featured == is_featured)
    return q.offset(skip).limit(limit).all()


def get_featured_resources(db: Session, skip: int = 0, limit: int = 10) -> List[Resource]:
    return db.query(Resource).filter(Resource.is_featured == True).offset(skip).limit(limit).all()