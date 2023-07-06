from pathlib import Path

from beaker import *
from pyteal import *

from utils import build


class MyStates:
    # Globla states
    total_supply = GlobalStateValue(
        stack_type=TealType.uint64, descr="The total supply available", default=Int(0)
    )
    reserve = GlobalStateValue(
        stack_type=TealType.uint64,
        descr="The remaining units available",
        default=Int(0),
    )
    asa_id = GlobalStateValue(
        stack_type=TealType.uint64, default=Int(0), descr="asset ID"
    )
    admin = GlobalStateValue(
        stack_type=TealType.bytes, descr="The admin address", default=Bytes("")
    )
    contract_addr = GlobalStateValue(
        stack_type=TealType.bytes, descr="The contract address", default=Bytes("")
    )

    # Local State
    balance = LocalStateValue(
        stack_type=TealType.uint64, descr="Wallet balance", default=Int(0)
    )


app = Application("Gunny_drop", state=MyStates())


@app.create
def create() -> Expr:
    return app.initialize_global_state()


@app.external(authorize=Authorize.only(Global.creator_address()))
def init(_total_supply: abi.Uint64, _asa_id: abi.Uint64) -> Expr:
    return Seq(
        app.state.total_supply.set(_total_supply.get()),
        app.state.reserve.set(_total_supply.get()),
        app.state.asa_id.set(_asa_id.get()),
        app.state.admin.set(Txn.sender()),
        app.state.contract_addr.set(Global.current_application_address()),
    )


@app.opt_in
def user_opt_in() -> Expr:
    return Seq(
        app.initialize_local_state(),
        # InnerTxnBuilder.Execute(
        #     {
        #         TxnField.type_enum: TxnType.Payment,
        #         TxnField.fee: Int(20000),
        #         TxnField.receiver: Txn.sender(),
        #         # TxnField.sender: Global.current_application_address(),
        #         TxnField.amount: Int(200000),
        #     }
        # ),
    )


@app.external(authorize=Authorize.only(Global.creator_address()))
def asa_opt_in(asset: abi.Asset) -> Expr:
    return Seq(
        InnerTxnBuilder.Execute(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.xfer_asset: asset.asset_id(),
                TxnField.asset_amount: Int(0),
            }
        ),
    )


@app.external
def claim_asset(asset: abi.Asset) -> Expr:
    return Seq(
        Assert(app.state.balance.get() == Int(0)),
        Assert(app.state.reserve.get() > Int(0)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(  # Transfer to MRB
            {
                TxnField.type_enum: TxnType.Payment,
                # TxnField.fee: Int(0),
                TxnField.receiver: Txn.sender(),
                TxnField.amount: Int(200000),
            }
        ),
        InnerTxnBuilder.Next(),
        # InnerTxnBuilder.SetFields(  # Inner Txn for Opt in
        #     {
        #         TxnField.type_enum: TxnType.AssetTransfer,
        #         # TxnField.fee: Int(0),
        #         TxnField.asset_receiver: Txn.sender(),
        #         TxnField.asset_sender: Txn.sender(),
        #         TxnField.xfer_asset: asset.asset_id(),
        #         TxnField.asset_amount: Int(0),
        #     }
        # ),
        # InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(  # Transaccion interna de envío de asset
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_amount: Int(1),
                TxnField.xfer_asset: app.state.asa_id.get(),
                TxnField.asset_receiver: Txn.sender(),
                # TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        app.state.balance.set(Int(1)),
        app.state.reserve.set(app.state.reserve.get() - Int(1)),
    )


@app.delete(bare=True, authorize=Authorize.only(Global.creator_address()))
def delete() -> Expr:
    return Approve()


if __name__ == "__main__":
    root_path = Path(__file__).parent
    build(root_path / "artifacts", app)
