"""
Regras de negócio para gestão de funcionários.
Usa o cliente admin (service_role) para criar/gerenciar usuários no Auth.
"""
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def listar_funcionarios() -> list[dict]:
    """
    Lista todos os perfis cadastrados no sistema.
    """
    resp = (
        _cliente()
        .table("perfis")
        .select("id, nome_completo, role, ativo, criado_em")
        .order("nome_completo")
        .execute()
    )
    return resp.data or []


def obter_funcionario(usuario_id: str) -> dict | None:
    resp = (
        _cliente()
        .table("perfis")
        .select("*")
        .eq("id", usuario_id)
        .single()
        .execute()
    )
    return resp.data if resp.data else None


def criar_funcionario(email: str, senha: str, nome_completo: str, role: str) -> dict:
    """
    Cria um novo usuário no Supabase Auth e um perfil na tabela 'perfis'.
    """
    email = email.strip().lower()
    nome_completo = nome_completo.strip()

    if not email or "@" not in email:
        raise ValueError("E-mail inválido.")
    if len(senha) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")
    if not nome_completo:
        raise ValueError("O nome completo é obrigatório.")
    if role not in ["admin", "funcionario"]:
        raise ValueError("Perfil inválido.")

    cli = _cliente()

    try:
        # 1. Cria o usuário no Supabase Auth
        resposta_auth = cli.auth.admin.create_user({
            "email": email,
            "password": senha,
            "email_confirm": True  # Confirma automaticamente
        })
        user_id = resposta_auth.user.id

        # 2. Cria o perfil na tabela pública
        cli.table("perfis").insert({
            "id": user_id,
            "nome_completo": nome_completo,
            "role": role,
            "ativo": True
        }).execute()

        return {"id": user_id, "email": email}

    except Exception as e:
        msg = str(e).lower()
        if "already registered" in msg or "email" in msg and "exist" in msg:
            raise ValueError("Este e-mail já está cadastrado no sistema.")
        raise ValueError(f"Erro ao criar usuário: {e}")


def editar_funcionario(usuario_id: str, nome_completo: str, role: str) -> dict:
    nome_completo = nome_completo.strip()
    if not nome_completo:
        raise ValueError("O nome completo é obrigatório.")
    if role not in ["admin", "funcionario"]:
        raise ValueError("Perfil inválido.")

    resp = (
        _cliente()
        .table("perfis")
        .update({"nome_completo": nome_completo, "role": role})
        .eq("id", usuario_id)
        .execute()
    )
    return resp.data[0] if resp.data else {}


def alternar_ativo(usuario_id: str) -> bool:
    """Inverte o status 'ativo' do perfil."""
    perfil = obter_funcionario(usuario_id)
    if not perfil:
        raise ValueError("Funcionário não encontrado.")

    novo_estado = not perfil["ativo"]
    _cliente().table("perfis").update({"ativo": novo_estado}).eq("id", usuario_id).execute()
    return novo_estado


def redefinir_senha(usuario_id: str, nova_senha: str):
    """Redefine a senha do usuário no Supabase Auth."""
    if len(nova_senha) < 6:
        raise ValueError("A nova senha deve ter pelo menos 6 caracteres.")

    try:
        _cliente().auth.admin.update_user_by_id(usuario_id, {"password": nova_senha})
    except Exception as e:
        raise ValueError(f"Erro ao redefinir senha: {e}")