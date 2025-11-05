from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app import crud, schemas
from app.database import get_db
from app.models import User
from app.auth_routes import get_current_user
from app.middleware.permissions import (
    require_user_permission,
    require_manager_permission,
    require_admin_permission
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.User)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息 - 所有用户"""
    return current_user


@router.put("/me", response_model=schemas.User)
def update_current_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新个人信息 - 所有用户"""
    require_user_permission()(current_user)
    
    # 用户只能修改自己的基本信息
    update_data = profile_update.dict(exclude_unset=True)
    updated_user = crud.update_user_profile(db, user_id=current_user.id, update_data=update_data)
    
    # 记录操作日志
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="profile_update",
        details=f"Updated profile fields: {list(update_data.keys())}"
    )
    
    return updated_user


@router.get("/", response_model=List[schemas.User])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有用户列表 - 管理员及以上"""
    require_admin_permission()(current_user)

    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/stats")
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息 - 管理员及以上"""
    require_admin_permission()(current_user)

    # 统计各角色用户数量
    total_users = db.query(User).filter(User.is_active == True).count()
    super_admin_count = db.query(User).filter(User.role == 'super_admin', User.is_active == True).count()
    admin_count = db.query(User).filter(User.role == 'admin', User.is_active == True).count()
    manager_count = db.query(User).filter(User.role == 'manager', User.is_active == True).count()
    user_count = db.query(User).filter(User.role == 'user', User.is_active == True).count()
    inactive_count = db.query(User).filter(User.is_active == False).count()

    return {
        "total_users": total_users,
        "role_distribution": {
            "super_admin": super_admin_count,
            "admin": admin_count,
            "manager": manager_count,
            "user": user_count
        },
        "inactive_count": inactive_count
    }


@router.get("/{user_id}", response_model=schemas.User)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户信息 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserManagementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    updated_user = crud.update_user(db, user_id=user_id, update_data=update_data)
    
    # 记录操作日志
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="user_update",
        details=f"Updated user {user.name}({user.userid}) fields: {list(update_data.keys())}"
    )
    
    return updated_user


@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户状态 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_active = status_data.get('is_active')
    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active field is required")
    
    # 防止管理员禁用自己
    if user_id == current_user.id and not is_active:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    
    updated_user = crud.update_user_status(db, user_id=user_id, is_active=is_active)
    
    # 记录操作日志
    action = "enabled" if is_active else "disabled"
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="user_status_change",
        details=f"{action.title()} user {user.name}({user.userid})"
    )
    
    return {
        "success": True,
        "message": f"User {action} successfully",
        "user_id": user_id,
        "new_status": is_active
    }


@router.get("/{user_id}/quotations", response_model=List[schemas.Quotation])
def get_user_quotations(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的报价列表 - 管理员及以上或本人"""
    # 权限检查：管理员可以查看所有人，用户只能查看自己的
    if current_user.role == "user" and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied: Can only view your own quotations")
    
    if current_user.role != "user":
        require_admin_permission()(current_user)
    
    quotations = crud.get_user_quotations(db, user_id=user_id, skip=skip, limit=limit)
    return quotations


@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户角色 - 超级管理员"""
    # 只有超级管理员可以修改用户角色
    if current_user.role != 'super_admin':
        raise HTTPException(status_code=403, detail="只有超级管理员可以修改用户角色")

    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 验证新角色是否有效
    valid_roles = ['user', 'manager', 'admin', 'super_admin']
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    # 防止超级管理员修改自己的角色
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own role")

    # 更新角色
    old_role = user.role
    user.role = new_role
    db.commit()
    db.refresh(user)

    # 记录操作日志
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="user_role_change",
        details=f"Changed user {user.name}({user.userid}) role from {old_role} to {new_role}"
    )

    return {
        "success": True,
        "message": f"用户角色已更新为 {new_role}",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": new_role
    }


@router.post("/sync-from-wecom")
def sync_users_from_wecom(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从企业微信同步用户列表 - 仅超级管理员"""
    # 只有超级管理员可以同步用户
    if current_user.role != 'super_admin':
        raise HTTPException(status_code=403, detail="只有超级管理员可以同步用户")

    try:
        from app.wecom_service import WecomService

        wecom_service = WecomService()

        # 从企业微信获取用户列表
        wecom_users = wecom_service.get_visible_users()

        if not wecom_users:
            return {
                "success": False,
                "message": "未能从企业微信获取用户列表，请检查应用权限配置",
                "stats": {
                    "total_wecom_users": 0,
                    "added": 0,
                    "updated": 0,
                    "deactivated": 0
                }
            }

        # 统计信息
        stats = {
            "total_wecom_users": len(wecom_users),
            "added": 0,
            "updated": 0,
            "deactivated": 0
        }

        # 获取企业微信中的所有userid
        wecom_userids = {user.get('userid') for user in wecom_users if user.get('userid')}

        # 遍历企业微信用户，新增或更新
        for wecom_user in wecom_users:
            userid = wecom_user.get('userid')
            if not userid:
                continue

            name = wecom_user.get('name', '')
            mobile = wecom_user.get('mobile', '')
            email = wecom_user.get('email', '')
            avatar = wecom_user.get('avatar', '')
            department = wecom_user.get('department', [])

            # 查找本地用户
            user = db.query(User).filter(User.userid == userid).first()

            if user:
                # 更新现有用户信息
                updated = False
                if user.name != name:
                    user.name = name
                    updated = True
                if user.mobile != mobile:
                    user.mobile = mobile
                    updated = True
                if user.email != email:
                    user.email = email
                    updated = True
                if user.avatar != avatar:
                    user.avatar = avatar
                    updated = True

                # 如果用户被禁用，重新激活
                if not user.is_active:
                    user.is_active = True
                    updated = True

                if updated:
                    stats['updated'] += 1
            else:
                # 创建新用户
                new_user = User(
                    userid=userid,
                    name=name,
                    mobile=mobile,
                    email=email,
                    avatar=avatar,
                    role='user',  # 默认角色为普通用户
                    is_active=True
                )
                db.add(new_user)
                stats['added'] += 1

        # 禁用不在企业微信中的用户
        all_local_users = db.query(User).filter(User.is_active == True).all()
        for user in all_local_users:
            if user.userid not in wecom_userids:
                user.is_active = False
                stats['deactivated'] += 1

        # 提交更改
        db.commit()

        # 记录操作日志
        crud.log_operation(
            db,
            user_id=current_user.id,
            operation="user_sync_from_wecom",
            details=f"从企业微信同步用户: 新增{stats['added']}人, 更新{stats['updated']}人, 禁用{stats['deactivated']}人"
        )

        return {
            "success": True,
            "message": f"同步完成：新增{stats['added']}人，更新{stats['updated']}人，禁用{stats['deactivated']}人",
            "stats": stats
        }

    except Exception as e:
        db.rollback()
        logger.error(f"从企业微信同步用户失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同步用户失败: {str(e)}"
        )