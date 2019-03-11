from pytest_factoryboy import register

from decisions.factories import (
    ActionFactory, CaseFactory, EventFactory, FunctionFactory,
    OrganizationClassFactory, OrganizationFactory, PostFactory)

register(ActionFactory)
register(CaseFactory)
register(FunctionFactory)
register(EventFactory)
register(OrganizationClassFactory)
register(OrganizationFactory)
register(PostFactory)
