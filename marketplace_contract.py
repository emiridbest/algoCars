from pyteal import *

class Product:
    class Variables:
        name = Bytes("NAME")
        image = Bytes("IMAGE")
        description = Bytes("DESCRIPTION")
        price = Bytes("PRICE")
        sold = Bytes("SOLD")

    class AppMethods:
        buy = Bytes("buy")

    def validate_string_input(self, string_input):
        return And(
            Gtxn[0].application_id() == Int(0),
            Gtxn[0].application_args[0] == Bytes("tutorial-marketplace:uv1"),
            Gtxn[0].application_args[1] == self.AppMethods.buy,
            Gtxn[0].application_args[2] == String(""),
            Gtxn[0].application_args[3] == String(""),
        )

    def application_creation(self):
        return Seq([
            Assert(Txn.application_args.length() == Int(4)),
            Assert(self.validate_string_input(Txn.application_args[0])),
            Assert(self.validate_string_input(Txn.application_args[1])),
            Assert(self.validate_string_input(Txn.application_args[2])),
            Assert(self.validate_string_input(Txn.application_args[3])),
            Assert(Btoi(Txn.application_args[3]) > Int(0)),
            App.globalPut(self.Variables.name, Txn.application_args[0]),
            App.globalPut(self.Variables.image, Txn.application_args[1]),
            App.globalPut(self.Variables.description, Txn.application_args[2]),
            App.globalPut(self.Variables.price, Btoi(Txn.application_args[3])),
            App.globalPut(self.Variables.sold, Int(0)),
            Approve()
        ])

    def buy(self):
        count = Txn.application_args[1]
        valid_number_of_transactions = Global.group_size() >= Int(1)
        valid_payment_to_seller = And(
            Gtxn[1].type_enum() == TxnType.Payment,
            Gtxn[1].receiver() == Global.creator_address(),
            Gtxn[1].amount() == App.globalGet(self.Variables.price) * Btoi(count),
            Gtxn[1].sender() == Gtxn[0].sender(),
        )
        can_buy = And(valid_number_of_transactions, valid_payment_to_seller)
        update_state = Seq([
            App.globalPut(self.Variables.sold, App.globalGet(self.Variables.sold) + Btoi(count)),
            Approve()
        ])
        return If(can_buy).Then(update_state).Else(Reject())

    def application_deletion(self):
        authorized_deletion = And(
            Gtxn[0].sender() == Global.creator_address(),
            Gtxn[0].application_args[0] == Bytes("delete_app")
        )
        return Return(authorized_deletion)

    def application_start(self):
        return Cond(
            [Txn.application_id() == Int(0), self.application_creation()],
            [Txn.on_completion() == OnComplete.DeleteApplication, self.application_deletion()],
            [Txn.application_args[0] == self.AppMethods.buy, self.buy()]
        )

    def approval_program(self):
        return self.application_start()

    def clear_program(self):
        return Return(Int(1))
