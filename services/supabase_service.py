"""
Serviço central de acesso ao Supabase.

Dois clientes são usados:
  - cliente_anon: respeita RLS, usa o token do usuário logado (sessão).
  - cliente_admin: ignora RLS (service_role). Usar APENAS no backend,
                   para operações administrativas explícitas e auditadas.
"""
from supabase import create_client, Client
from config import Config

# Cliente com permissões públicas (respeita RLS)
_cliente_anon: Client | None = None

# Cliente com permissões totais (SERVICE ROLE — nunca expor!)
_cliente_admin: Client | None = None


def init_supabase():
    """Inicializa ambos os clientes. Chamada no create_app()."""
    global _cliente_anon, _cliente_admin

    if _cliente_anon is None:
        _cliente_anon = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_ANON_KEY,
        )

    if _cliente_admin is None:
        _cliente_admin = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_SERVICE_ROLE_KEY,
        )


def get_cliente_anon() -> Client:
    """Cliente que respeita as políticas RLS. Use para operações do usuário."""
    if _cliente_anon is None:
        raise RuntimeError("Supabase anon client não inicializado.")
    return _cliente_anon


def get_cliente_admin() -> Client:
    """
    Cliente com service_role. NUNCA use para servir dados diretamente ao navegador.
    Use apenas para operações administrativas auditadas no backend.
    """
    if _cliente_admin is None:
        raise RuntimeError("Supabase admin client não inicializado.")
    return _cliente_admin


def autenticar(email: str, senha: str):
    """
    Autentica o usuário com email + senha via Supabase Auth.

    Cria um cliente descartável para evitar conflito entre sessões
    simultâneas (o cliente_anon global guardaria o token do último login,
    o que causaria vazamento entre usuários diferentes).

    Retorna a resposta (com access_token, refresh_token, user).
    Levanta exceção em caso de falha.
    """
    cliente_temp = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
    resposta = cliente_temp.auth.sign_in_with_password({
        "email": email,
        "password": senha,
    })
    return resposta


def obter_perfil(usuario_id: str):
    """
    Busca o perfil (role, nome, ativo) do usuário na tabela public.perfis.

    Usa o cliente admin porque:
      1) A identidade já foi validada pelo Supabase Auth antes desta chamada.
      2) O RLS da tabela perfis permite SELECT apenas do próprio perfil,
         mas queremos garantir o retorno mesmo com configurações restritivas.
      3) Esta chamada é feita somente no backend após login bem-sucedido.
    """
    cliente = get_cliente_admin()
    resposta = (
        cliente.table("perfis")
        .select("*")
        .eq("id", usuario_id)
        .single()
        .execute()
    )
    return resposta.data if resposta.data else None