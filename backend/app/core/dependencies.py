import uuid

import jwt

from fastapi import Depends, HTTPException, status

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from app.core.security import SECRET_KEY, ALGORITHM

from app.database import get_db

from app.models import User

security = HTTPBearer()

def get_current_user(

    credentials: HTTPAuthorizationCredentials = Depends(security),

    db: Session = Depends(get_db),

) -> User:

    token = credentials.credentials

    try:

        payload = jwt.decode(

            token,

            SECRET_KEY,

            algorithms=[ALGORITHM],

        )

        user_id = payload.get("sub")

        if not user_id:

            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail="Invalid token",

            )

        user_uuid = uuid.UUID(user_id)

    except (jwt.InvalidTokenError, ValueError):

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid or expired token",

        )

    user = db.query(User).filter(User.id == user_uuid).first()

    if not user or not user.is_active:

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="User not found or inactive",

        )

    return user