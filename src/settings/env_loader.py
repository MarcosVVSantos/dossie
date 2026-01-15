from __future__ import annotations
from pathlib import Path
import os
from dotenv import load_dotenv, find_dotenv
import sys
from typing import Iterable, Optional, Dict


def find_env_file(path: Optional[str] = None, env_var: str = "ENV_PATH") -> Optional[Path]:
    """Tenta localizar o arquivo .env com a seguinte ordem:
    1. argumento `path` se fornecido
    2. variável de ambiente `ENV_PATH`
    3. dotenv.find_dotenv()
    4. tentativa de procurar em project root (caminho relativo a este arquivo)
    Retorna Path ou None se não encontrado.
    """
    # 1. argumento direto
    if path:
        p = Path(path).expanduser()
        if p.exists():
            return p

    # 2. ENV_PATH
    env_path = os.environ.get(env_var)
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return p

    # 3. find_dotenv
    found = find_dotenv()
    if found:
        p = Path(found)
        if p.exists():
            return p

    # 4. procurar em lugares comuns (project root relativo a este arquivo)
    candidate = Path(__file__).resolve().parents[3] / ".env"
    if candidate.exists():
        return candidate

    return None


def load_env(path: Optional[str] = None, required_vars: Optional[Iterable[str]] = None, verbose: bool = False) -> Dict[str, Optional[str]]:
    """Carrega o .env encontrado e valida variáveis obrigatórias.

    - path: caminho explícito para o arquivo .env (opcional)
    - required_vars: lista de nomes obrigatórios; se qualquer um faltar, lança RuntimeError
    - verbose: imprime onde foi carregado e quais variáveis estão faltando

    Retorna um dicionário com os valores das variáveis solicitadas (ou todas se required_vars for None).
    """
    env_file = find_env_file(path=path)

    if env_file:
        load_dotenv(dotenv_path=str(env_file))
        if verbose:
            print(f"🔎 Usando .env em: {env_file}")
    else:
        if verbose:
            print("⚠️ Nenhum arquivo .env encontrado (procure por .env ou defina ENV_PATH). Continuando — as variáveis podem estar definidas no ambiente.")

    # Validar variáveis obrigatórias
    missing = []
    values = {}
    if required_vars:
        for name in required_vars:
            val = os.environ.get(name)
            values[name] = val
            if val in (None, ""):
                missing.append(name)

    if missing:
        message = (
            f"Faltando variáveis de ambiente obrigatórias: {', '.join(missing)}."
            " Copie `.env.example` para `.env` e preencha as chaves, ou exporte as variáveis no ambiente."
        )
        raise RuntimeError(message)

    # Se não pediu required_vars, retorna todas variáveis do env (útil para debug)
    if not required_vars:
        # Retorna apenas as variáveis lidas do ambiente (padrão)
        return dict(os.environ)

    return values


# Pequeno utilitário executável para debug / CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carregar e validar .env")
    parser.add_argument("--env", help="Caminho para o .env (opcional)")
    parser.add_argument("--vars", help="Variáveis obrigatórias separadas por vírgula", default="")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    required = [v.strip() for v in args.vars.split(",") if v.strip()]
    try:
        out = load_env(path=args.env, required_vars=required or None, verbose=args.verbose)
        print("OK - variáveis carregadas")
    except Exception as e:
        print("Erro:", e)
        sys.exit(1)
