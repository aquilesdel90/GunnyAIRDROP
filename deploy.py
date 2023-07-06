from pathlib import Path

from beaker import client, sandbox

from app import app
from utils import build

root_path = Path(__file__).parent
build(root_path / "artifacts", app)

accounts = sandbox.kmd.get_accounts()
sender = accounts[0]

app_client = client.ApplicationClient(
    client=sandbox.get_algod_client(),
    app=app,
    sender=sender.address,
    signer=sender.signer,
)

app_client.create()
app_client.fund(10000000)  # adds 10 Algos to the S.C.

# return_value = app_client.call(hello, name="").return_value
# print(return_value)

print("Contract ID: {}", app_client.app_id)
print("Contract Addr: {}", app_client.app_addr)
print("Account info: {}", app_client.get_application_account_info())
print("Creator: {}", sender)
