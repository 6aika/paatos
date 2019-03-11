import factory
from faker import Faker

from decisions.models import Organization, OrganizationClass, Post

fake = Faker()
fake.seed(7)


class OrganizationClassFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationClass

    id = 1
    name = fake.company_suffix()


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = fake.company()
    classification = factory.SubFactory(OrganizationClassFactory)
    founding_date = fake.date_time_this_century(before_now=True, after_now=False)


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    label = fake.word()
    organization = factory.SubFactory(OrganizationFactory)
    start_date = fake.date_time_this_century(before_now=True, after_now=False)
