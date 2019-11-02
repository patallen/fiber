from dataclasses import dataclass, asdict
import datetime


@dataclass
class Serializable:
    def to_dict(self):
        raise NotImplementedError


@dataclass
class CashFlowStatement(Serializable):
    date: datetime.date
    depam: float
    stock_comp: float
    op_flow: float
    cap_exp: float
    acq_disp: float
    inv_trading: float
    inv_cf: float
    debt_issuance: float
    buyback_issuance: float
    div_payments: float
    financing_cf: float
    forex_effect: float
    net_cf: float
    free_cf: float
    marketcap: float

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, adict):
        return cls(
            date=datetime.date.fromisoformat(adict["date"]),
            depam=float(adict["Depreciation & Amortization"]),
            stock_comp=float(adict["Stock-based compensation"]),
            op_flow=float(adict["Operating Cash Flow"]),
            cap_exp=float(adict["Capital Expenditure"]),
            acq_disp=float(adict["Acquisitions and disposals"]),
            inv_trading=float(adict["Investment purchases and sales"]),
            inv_cf=float(adict["Investing Cash flow"]),
            debt_issuance=float(adict["Issuance (repayment) of debt"]),
            buyback_issuance=float(adict["Issuance (buybacks) of shares"]),
            div_payments=float(adict["Dividend payments"]),
            financing_cf=float(adict["Financing Cash Flow"]),
            forex_effect=float(adict["Effect of forex changes on cash"]),
            net_cf=float(adict["Net cash flow / Change in cash"]),
            free_cf=float(adict["Free Cash Flow"]),
            marketcap=float(adict["Net Cash/Marketcap"]),
        )
