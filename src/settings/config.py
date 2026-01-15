from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Optional
from .env_loader import load_env


@dataclass
class Config:
    # Auth
    email: str
    password: str
    client_id: str = "mottu-admin"
    grant_type: str = "password"
    auth_url: str = "https://sso.mottu.cloud/realms/Internal/protocol/openid-connect/token"

    # Backend
    backendUrl: str = "https://backend.mottu.cloud/api/v2"
    cnh_url_template: str = "{backend}/UsuarioCnh/BuscarUrlCnh/{}?fullUrl=true"
    paymentsUrl: Optional[str] = None

    # Paths
    excel: Path = Path("src/utils/Relatório BOs.xlsx")
    output_dir: Path = Path("src/output/gerador/cnh")
    contract_path: Path = Path("src/output/gerador/contract")

    # Behavior
    maxRetries: int = 3
    backoff: int = 5

    # Other
    imageProcessUrl: Optional[str] = None
    fileToolsUrl: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        required = ["email", "password"]
        # load_env validates presence of required vars and raises RuntimeError if missing
        load_env(required_vars=required, verbose=False)

        # read values with fallbacks
        email = os.environ.get("email")
        password = os.environ.get("password")
        client_id = os.environ.get("client_id", cls.client_id)
        grant_type = os.environ.get("grant_type", cls.grant_type)
        auth_url = os.environ.get("auth_url", cls.auth_url)

        backend = os.environ.get("backendUrl", cls.backendUrl)
        cnh_template = os.environ.get("cnh_url_template", backend + '/UsuarioCnh/BuscarUrlCnh/{}?fullUrl=true')
        payments = os.environ.get("paymentsUrl")

        excel = Path(os.environ.get("excel", str(cls.excel))).resolve()
        output_dir = Path(os.environ.get("saida", str(cls.output_dir))).resolve()
        contract_path = Path(os.environ.get("CONTRACT_PATH", str(cls.contract_path))).resolve()

        maxRetries = int(os.environ.get("maxRetries", str(cls.maxRetries)))
        backoff = int(os.environ.get("backoff", str(cls.backoff)))

        imageProcessUrl = os.environ.get("imageProcessUrl")
        fileToolsUrl = os.environ.get("fileToolsUrl")

        return cls(
            email=email,
            password=password,
            client_id=client_id,
            grant_type=grant_type,
            auth_url=auth_url,
            backendUrl=backend,
            cnh_url_template=cnh_template,
            paymentsUrl=payments,
            excel=excel,
            output_dir=output_dir,
            contract_path=contract_path,
            maxRetries=maxRetries,
            backoff=backoff,
            imageProcessUrl=imageProcessUrl,
            fileToolsUrl=fileToolsUrl,
        )


# singleton config instance loaded at import time
try:
    config = Config.from_env()
except Exception:
    # If env is not present, we still expose a config object with defaults
    # so modules can import it without crashing; accessors should handle missing critical values.
    config = Config(
        email=os.environ.get("email", ""),
        password=os.environ.get("password", ""),
    )
