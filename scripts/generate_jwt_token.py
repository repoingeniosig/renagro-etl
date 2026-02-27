#!/usr/bin/env python3
"""
Genera tokens JWT para autenticación con PostgREST.

Uso:
  python scripts/generate_jwt_token.py
  python scripts/generate_jwt_token.py --secret "mi-secreto" --role api_user --exp 24

Requiere: pip install PyJWT
"""

import argparse
import datetime
import os
import sys

try:
    import jwt
except ImportError:
    print("Error: PyJWT no está instalado. Ejecutar: pip install PyJWT")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv es opcional


def _get_default_secret() -> str:
    """Obtiene el secret desde la variable de entorno POSTGREST_JWT_SECRET."""
    secret = os.environ.get("POSTGREST_JWT_SECRET")
    if not secret:
        print("Error: POSTGREST_JWT_SECRET no está definido en .env")
        sys.exit(1)
    return secret


def generate_token(secret: str, role: str, expiration_hours: int) -> str:
    """Genera un token JWT con el rol y expiración especificados."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(hours=expiration_hours),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def decode_token(secret: str, token: str) -> dict:
    """Decodifica un token JWT para verificación."""
    return jwt.decode(token, secret, algorithms=["HS256"])


def main():
    parser = argparse.ArgumentParser(
        description="Genera tokens JWT para autenticación con PostgREST"
    )
    parser.add_argument(
        "--secret",
        default=None,
        help="JWT secret (si no se especifica, se lee de .env / POSTGREST_JWT_SECRET)",
    )
    parser.add_argument(
        "--role",
        default="api_user",
        help="Rol PostgreSQL para el token (default: api_user)",
    )
    parser.add_argument(
        "--exp",
        type=int,
        default=24,
        help="Horas de expiración del token (default: 24)",
    )
    parser.add_argument(
        "--verify",
        metavar="TOKEN",
        help="Verificar y decodificar un token existente",
    )

    args = parser.parse_args()
    secret = args.secret or _get_default_secret()

    if args.verify:
        try:
            decoded = decode_token(secret, args.verify)
            print("Token válido:")
            print(f"  Rol: {decoded.get('role')}")
            exp = datetime.datetime.fromtimestamp(
                decoded.get("exp", 0), tz=datetime.timezone.utc
            )
            print(f"  Expira: {exp.isoformat()}")
        except jwt.ExpiredSignatureError:
            print("Error: Token expirado")
            sys.exit(1)
        except jwt.InvalidTokenError as e:
            print(f"Error: Token inválido - {e}")
            sys.exit(1)
        return

    token = generate_token(secret, args.role, args.exp)

    print(f"JWT Token (rol={args.role}, expira en {args.exp}h):\n")
    print(token)
    print(f"\nUso con curl:")
    print(
        f'  curl -H "Authorization: Bearer {token}" '
        f"http://localhost:3000/rpc/get_boletas_aprobadas?p_limit=10"
    )


if __name__ == "__main__":
    main()
