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
        updatePrice = Bytes("updatePrice")

    def input_validation(self, method):
        if method == self.AppMethods.buy:
            valid_args = And(
                Txn.application_args.length() == Int(4),
                Txn.application_args[0] == self.AppMethods.buy,
                Btoi(Txn.application_args[3]) > Int(0)
            )
            return valid_args
        elif method == self.AppMethods.updatePrice:
            valid_args = And(
                Txn.application_args.length() == Int(2),
                Txn.application_args[0] == self.AppMethods.updatePrice,
                Btoi(Txn.application_args[1]) > Int(0)
            )
            return valid_args
        else:
            return False

    def authentication(self, method):
        if method == self.AppMethods.updatePrice:
            valid_sender = Txn.sender() == Global.creator_address()
            return valid_sender
        else:
            return True

    def buy(self):
        count = Btoi(Txn.application_args[1])
        valid_number_of_transactions = Global.group_size() == Int(2)
        valid_payment_to_seller = And(
            Gtxn[1].type_enum() == TxnType.Payment,
            Gtxn[1].receiver() == Global.creator_address(),
            Gtxn[1].amount() == App.globalGet(self.Variables.price) * count,
            Gtxn[1].sender() == Gtxn[0].sender(),
        )
        can_buy = And(valid_number_of_transactions,
                      valid_payment_to_seller)
        update_state = Seq([
            App.globalPut(self.Variables.sold, App.globalGet(self.Variables.sold) + count),
            Approve()
        ])
        return If(can_buy).Then(update_state).Else(Reject())

    def updatePrice(self):
        new_price = Btoi(Txn.application_args[1])
        if new_price > Int(0):
            App.globalPut(self.Variables.price, new_price)
            return Approve()
        else:
            return Reject()

    def application_creation(self):
        return Seq([
            Assert(Txn.application_args.length() == Int(4)),
            Assert(Txn.note() == Bytes("tutorial-marketplace:uv1")),
            Assert(Btoi(Txn.application_args[3]) > Int(0)),
            App.globalPut(self.Variables.name, Txn.application_args[0]),
            App.globalPut(self.Variables.image, Txn.application_args[1]),
            App.globalPut(self.Variables.description, Txn.application_args[2]),
            App.globalPut(self.Variables.price, Btoi(Txn.application_args[3])),
            App.globalPut(self.Variables.sold, Int(0)),
            Approve()
        ])

    def application_deletion(self):
        return Return(Txn.sender() == Global.creator_address())

    def application_start(self):
        method = Txn.application_args[0]

        if not self.input_validation(method):
            return Reject()

        if not self.authentication(method):
            return Reject()

        if method == self.AppMethods.buy:
            return self.buy()
        elif method == self.AppMethods.updatePrice:
            return self.updatePrice()
        else:
            return Reject()

    def approval_program(self):
        return self.application_start()

    def clear_program(self):
        return Return(Int(1))
