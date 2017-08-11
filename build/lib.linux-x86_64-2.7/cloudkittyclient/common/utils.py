# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import print_function

import datetime
import sys
import textwrap
import uuid

from oslo_serialization import jsonutils
from oslo_utils import encodeutils
from oslo_utils import importutils
import prettytable
import six

from cloudkittyclient import exc
from cloudkittyclient.i18n import _
from cloudkittyclient.openstack.common import cliutils
from prettytable import PrettyTable
import json
import simplejson as json
import prettytable

def import_versioned_module(version, submodule=None):
    module = 'cloudkittyclient.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)


# Decorator for cli-args
def arg(*args, **kwargs):
    def _decorator(func):
        if 'help' in kwargs:
            if 'default' in kwargs:
                kwargs['help'] += " Defaults to %s." % kwargs['default']
            required = kwargs.get('required', False)
            if required:
                kwargs['help'] += " required."
            elif 'default' not in kwargs:
                kwargs['help'] += "."

        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, field_labels, formatters={}, sortby=0):

    def _make_default_formatter(field):
        return lambda o: getattr(o, field, '')

    new_formatters = {}
    for field, field_label in six.moves.zip(fields, field_labels):
        if field in formatters:
            new_formatters[field_label] = formatters[field]
        else:
            new_formatters[field_label] = _make_default_formatter(field)

    cliutils.print_list(objs, field_labels,
                        formatters=new_formatters,
                        sortby_index=sortby)


def nested_list_of_dict_formatter(field, column_names):
    # (TMaddox) Because the formatting scheme actually drops the whole object
    # into the formatter, rather than just the specified field, we have to
    # extract it and then pass the value.
    return lambda o: format_nested_list_of_dict(getattr(o, field),
                                                column_names)


def format_nested_list_of_dict(l, column_names):
    pt = prettytable.PrettyTable(caching=False, print_empty=False,
                                 header=True, hrules=prettytable.FRAME,
                                 field_names=column_names)
    for d in l:
        pt.add_row(list(map(lambda k: d[k], column_names)))
    return pt.get_string()


def print_dict(d, dict_property="Property", wrap=0):
    pt = prettytable.PrettyTable([dict_property, 'Value'], print_empty=False)
    pt.align = 'l'
    for k, v in sorted(six.iteritems(d)):
        # convert dict to str to check length
        if isinstance(v, dict):
            v = jsonutils.dumps(v)
        # if value has a newline, add in multiple rows
        # e.g. fault with stacktrace
        if v and isinstance(v, six.string_types) and r'\n' in v:
            lines = v.strip().split(r'\n')
            col1 = k
            for line in lines:
                if wrap > 0:
                    line = textwrap.fill(str(line), wrap)
                pt.add_row([col1, line])
                col1 = ''
        else:
            if wrap > 0:
                v = textwrap.fill(str(v), wrap)
            pt.add_row([k, v])
    encoded = encodeutils.safe_encode(pt.get_string())
    # FIXME(gordc): https://bugs.launchpad.net/oslo-incubator/+bug/1370710
    if six.PY3:
        encoded = encoded.decode()
    print(encoded)


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exc.HTTPNotFound:
        pass

    # now try to get entity as uuid
    try:
        uuid.UUID(str(name_or_id))
        return manager.get(name_or_id)
    except (ValueError, exc.HTTPNotFound):
        pass

    # finally try to find entity by name
    try:
        return manager.find(name=name_or_id)
    except exc.HTTPNotFound:
        msg = _("No %(name)s with a name or ID of '%(id)s' exists.") % {
            "name": manager.resource_class.__name__.lower(),
            "id": name_or_id
        }
        raise exc.CommandError(msg)


def args_array_to_dict(kwargs, key_to_convert):
    values_to_convert = kwargs.get(key_to_convert)
    if values_to_convert:
        try:
            kwargs[key_to_convert] = dict(v.split("=", 1)
                                          for v in values_to_convert)
        except ValueError:
            msg = _("%(key)s must be a list of key=value "
                    "not '%(value)s'") % {
                "key": key_to_convert,
                "value": values_to_convert
            }
            raise exc.CommandError(msg)
    return kwargs


def args_array_to_list_of_dicts(kwargs, key_to_convert):
    """Converts ['a=1;b=2','c=3;d=4'] to [{a:1,b:2},{c:3,d:4}]."""
    values_to_convert = kwargs.get(key_to_convert)
    if values_to_convert:
        try:
            kwargs[key_to_convert] = []
            for lst in values_to_convert:
                pairs = lst.split(";")
                dct = dict()
                for pair in pairs:
                    kv = pair.split("=", 1)
                    dct[kv[0]] = kv[1].strip(" \"'")  # strip spaces and quotes
                kwargs[key_to_convert].append(dct)
        except Exception:
            msg = _("%(key)s must be a list of "
                    "key1=value1;key2=value2;... not '%(value)s'") % {
                "key": key_to_convert,
                "value": values_to_convert
            }
            raise exc.CommandError(msg)
    return kwargs


def key_with_slash_to_nested_dict(kwargs):
    nested_kwargs = {}
    for k in list(kwargs):
        keys = k.split('/', 1)
        if len(keys) == 2:
            nested_kwargs.setdefault(keys[0], {})[keys[1]] = kwargs[k]
            del kwargs[k]
    kwargs.update(nested_kwargs)
    return kwargs


def merge_nested_dict(dest, source, depth=0):
    for (key, value) in six.iteritems(source):
        if isinstance(value, dict) and depth:
            merge_nested_dict(dest[key], value,
                              depth=(depth - 1))
        else:
            dest[key] = value


def ts2dt(timestamp):
    """timestamp to datetime format."""
    if not isinstance(timestamp, float):
        timestamp = float(timestamp)
    return datetime.datetime.utcfromtimestamp(timestamp)


def exit(msg=''):
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(1)

# process updated values from client
def process_updated_values(data):

   print("Invoice updated succesfully, Details were as follows:")
   invoice_updated = data
   for data in invoice_updated:
        print(data + " \tis updated")


# Process invoice dict and display
# Tabulated display using Pretty table
def process_dict_and_display(invoice):

    # class for formatting
    class color:
        BOLD = '\033[1m'
        END = '\033[0m'

    print(invoice)
    for tenant_data in invoice:

        # initialize table and table field names
        x = PrettyTable()
        x.field_names = ["id", "date", "from", "to", "total", "paid", "bal", "tenant(T)", "T ID","status" ]

        invoice_date = tenant_data.invoice_date
        balance_cost = tenant_data.balance_cost
        tenant_name = tenant_data.tenant_name
        paid_cost = tenant_data.paid_cost
        total_cost = tenant_data.total_cost
        invoice_id = tenant_data.invoice_id
        tenant_id = tenant_data.tenant_id
        invoice_period_from = tenant_data.invoice_period_from
        invoice_period_to = tenant_data.invoice_period_to
        payment_status = tenant_data.payment_status
        id = tenant_data.id
        invoice_data = tenant_data.invoice_data

        x.add_row([invoice_id, invoice_date, invoice_period_from, invoice_period_to, total_cost, paid_cost, balance_cost, tenant_name, tenant_id, payment_status])
        print(x)

        # invoke next table y
        y = PrettyTable()

        # itemized Invoice details of the particular tenant
        for invoice_data_entity,value in invoice_data.iteritems():

                # Invoice_data_entity details
                # For make user to understand the case well
                invoice_data_entity_list = {
                        'dict_all_cost_total': 'Total Cost for tenant based on all instances',
                        'dict_total_all': 'Total Cost for Instance',
                        'dict_inbound': 'Inbound charges for Instance',
                        'dict_volume': 'Volume Charges',
                        'dict_compute': 'Compute Charges for Instance',
                        'dict_floating': 'Floating IP Charges',
                        'dict_outbound': 'Outbound Charges for Instance',
                        'dict_cloud_storage': 'cloud storage charges(Swift)',
                        'dict_instance_addon': 'instance addon charges',
                }

                # If value is Dict (Itemized invoice)
                if type(value) is dict:

                        # get the instance id and other instance and cost details
                        for instance_id,details in value.iteritems():

                                # variables for necessary items
                                entity_name = invoice_data_entity_list[invoice_data_entity]
                                instance_id = instance_id
                                instance_name = details[0]
                                instance_size = details[1]
                                cost = details[2]

                                # field names and add values to rows
                                y.field_names = ["cost for entity","instance id","instance_name","instance_size","cost"]
                                y.add_row([entity_name, instance_id, instance_name, instance_size, cost])

                # if value not dict(simple datas only entity and cost)
                else:

                        # variables for necessary items
                        entity_name = invoice_data_entity_list[invoice_data_entity]
                        cost = value

                        # field names and add values to rows
                        y.field_names = ["cost for entity","instance id","instance_name","instance_size","cost"]
                        y.add_row([entity_name,"-", "-", "-", cost])

        print("Itemized invoice break up for invoice %s" % invoice_id)
        print(y)
        print(color.END)


# Process dict and display just invoice basic details
def process_dict_and_display_invoice_list(invoice):
    # class for formatting
    class color:
        BOLD = '\033[1m'
        END = '\033[0m'

    for tenant_data in invoice:

        # initialize table and table field names
        x = PrettyTable()
        x.field_names = ["id", "date", "from", "to", "total", "paid", "bal", "tenant(T)", "T ID","status" ]

        invoice_date = tenant_data.invoice_date
        balance_cost = tenant_data.balance_cost
        tenant_name = tenant_data.tenant_name
        paid_cost = tenant_data.paid_cost
        total_cost = tenant_data.total_cost
        invoice_id = tenant_data.invoice_id
        tenant_id = tenant_data.tenant_id
        invoice_period_from = tenant_data.invoice_period_from
        invoice_period_to = tenant_data.invoice_period_to
        payment_status = tenant_data.payment_status
        id = tenant_data.id
        invoice_data = tenant_data.invoice_data

        x.add_row([invoice_id, invoice_date, invoice_period_from, invoice_period_to, total_cost, paid_cost, balance_cost, tenant_name, tenant_id, payment_status])
        print(x)
