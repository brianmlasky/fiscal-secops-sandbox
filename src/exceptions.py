class FiscalGovernanceError(Exception): pass
class GovernancePlaneError(FiscalGovernanceError): pass
class InsufficientFundsError(FiscalGovernanceError): pass
