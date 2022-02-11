# make security resources private or public using view_resourcebase permission
#
# Usage:
#   manage.py shell
#   execfile('scripts/misc-dodiws/make_security_resources_private.py')
#   make_security_resources_private()
#   make_security_resources_public()

from django.contrib.auth.models import Group
from geonode.base.models import ResourceBase
from guardian.models import GroupObjectPermission
from guardian.shortcuts import assign_perm, remove_perm

# hardcoded to be used later
# resources that originally private
# originally found using private_security_resources query below with exclude_ids=[]
exclude_ids = [3409, 5020]

# category security(sec-01) and incidents(sec-02) in base_topiccategory table
security_identifiers = ['sec-01', 'sec-02']

anonymous_group = Group.objects.get(name='anonymous')
public_permission_resources_pk = GroupObjectPermission.objects\
    .filter(permission__codename='view_resourcebase', group=anonymous_group, content_type__model='resourcebase')\
    .extra({'object_pk_int': "CAST(object_pk as INTEGER)"})\
    .values('object_pk_int')
security_resources = ResourceBase.objects.filter(category__identifier__in=security_identifiers).exclude(pk__in=exclude_ids)
public_security_resources = security_resources.filter(pk__in=public_permission_resources_pk)
private_security_resources = security_resources.exclude(pk__in=public_permission_resources_pk)


def make_security_resources_public():
    for resource in private_security_resources:
        assign_perm('view_resourcebase', anonymous_group, resource.get_self_resource())


def make_security_resources_private():
    for resource in public_security_resources:
        remove_perm('view_resourcebase', anonymous_group, resource.get_self_resource())
