from app.settings import settings
from app.oracle.client import OracleClient, OracleConnectionError
import json

cli = OracleClient(
    settings.ORACLE_RPC_URL,
    settings.ORACLE_CONTRACT_ADDRESS,
    settings.ORACLE_CONTRACT_JSON_PATH,
    private_key=settings.ORACLE_PRIVATE_KEY or None,
)
print('connected:', cli.is_connected())
try:
    latest = cli.call_readonly('latestRound')
    print('latestRound:', latest)
    data = cli.get_round_struct(int(latest))
    def normalize(v):
        if isinstance(v, bytes):
            return '0x' + v.hex()
        try:
            return int(v)
        except Exception:
            return str(v)
    print(json.dumps({k: normalize(v) for k,v in data.items()}, indent=2))
except OracleConnectionError as e:
    print('OracleConnectionError:', e)
except Exception as e:
    print('Error:', e)
