# Copyright 2015 Objectif Libre
#
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
from cloudkittyclient.common import utils

def do_report_tenant_list(cc, args):
    """List tenant report."""
    tenants = cc.reports.list_tenants()
    out_table = utils.prettytable.PrettyTable()
    out_table.add_column("Tenant UUID", tenants)
    print(out_table)

# invoice add arguments
@utils.arg('-i', '--invoice-id',
           help='invoice-id',
           required=True)
@utils.arg('-d','--invoice-date',
           help='invoice-date',
           required=True)
@utils.arg('-if','--invoice-period-from',
           help='invoice-date',
           required=True)
@utils.arg('-it','--invoice-period-to',
           help='invoice-date',
           required=True)
@utils.arg('-ti','--tenant',
           help='tenant-id',
           required=True)
@utils.arg('-da','--invoice-data',
           help='invoice-data',
           required=True)
@utils.arg('-tn','--tenant-name',
           help='tenant-name',
           required=True)
@utils.arg('-tc','--total-cost',
           help='total-cost',
           required=True)
@utils.arg('-pc','--paid-cost',
           help='paid-cost',
           required=True)
@utils.arg('-bc','--balance-cost',
           help='balance-cost',
           required=True)
@utils.arg('-ps','--payment-status',
           help='payment-status',
           required=True)

# invoice add function
def do_invoice_add(cc, args):
    """Add invoice details to table"""

    invoice_period_from = utils.ts2dt(args.invoice_period_from) if args.invoice_period_from else None
    invoice_period_to = utils.ts2dt(args.invoice_period_to) if args.invoice_period_to else None
    invoice_date = utils.ts2dt(args.invoice_date) if args.invoice_date else None

    # invoice arguments
    kwargs = {
                "invoice_id":args.invoice_id,
                "invoice_date":invoice_date,
                "invoice_period_from":invoice_period_from,
                "invoice_period_to":invoice_period_to,
                "tenant_id":args.tenant,
                "invoice_data":args.invoice_data,
                "tenant_name":args.tenant_name,
                "total_cost":args.total_cost,
                "paid_cost":args.paid_cost,
                "balance_cost":args.balance_cost,
                "payment_status":args.payment_status
             }

    out = cc.reports.add_invoice(**kwargs)


@utils.arg('-a', '--all-tenants',
           help='All tenants details',
           required=False,
           nargs='?',
           const=1,
           default=0)

def do_invoice_list(cc, args):
    """List the invoices accepts all-tenants arg"""

    # Invoice details as Unicode response
    invoice = cc.reports.list_invoice(all_tenants=args.all_tenants)
    utils.process_dict_and_display_invoice_list(invoice)


@utils.arg('invoice_id',
           help='input for invoice id or name',
           nargs='?')

def do_invoice_show(cc, args):
    """Show the invoice details for provided invoice"""

    # Invoice details as Unicode response
    invoice = cc.reports.show_invoice(invoice_id=args.invoice_id)
    utils.process_dict_and_display(invoice)


@utils.arg('-t', '--tenant-id',
           help='Tenant id',
           required=False,
           dest='total_tenant_id')
@utils.arg('-v', '--invoice-id',
           help='invoice_id',
           required=False)
@utils.arg('-ps', '--payment-status',
           help='payment_status',
           required=False)

def do_invoice_get(cc, args):
    """Get invoice based on tenant-id, invoice-id and payment_status args."""

    # Invoice details as Unicode response
    invoice = cc.reports.get_invoice(tenant_id=args.total_tenant_id,
                                   invoice_id=args.invoice_id,
                                   payment_status = args.payment_status)
    utils.process_dict_and_display(invoice)


@utils.arg('-t', '--tenant-id',
           help='Tenant id',
           required=False,
           dest='total_tenant_id')
@utils.arg('-b', '--begin',
           help='Begin timestamp',
           required=False)
@utils.arg('-e', '--end',
           help='End timestamp',
           required=False)
@utils.arg('-s', '--service',
           help='Service Type',
           required=False)
@utils.arg('-i', '--instance-id',
           help='instance_id',
           required=False)

def do_total_get(cc, args):
    """Get total reports."""
    begin = utils.ts2dt(args.begin) if args.begin else None
    end = utils.ts2dt(args.end) if args.end else None
    total = cc.reports.get_total(tenant_id=args.total_tenant_id,
                                 begin=begin,
                                 end=end,
                                 service=args.service,
                                 instance_id=args.instance_id)
    utils.print_dict({'Total': total or 0.0})


@utils.arg('-v', '--invoice-id',
           help='invoice_id',
           required=False)
@utils.arg('-tc','--total-cost',
           help='total-cost',
           required=False)
@utils.arg('-pc','--paid-cost',
           help='paid-cost',
           required=False)
@utils.arg('-bc','--balance-cost',
           help='balance-cost',
           required=False)
@utils.arg('-ps','--payment-status',
           help='payment-status',
           required=False)

def do_invoice_update(cc, args):
    """ Update invoice details."""

    # invoice arguments
    kwargs = {
                "invoice_id":args.invoice_id if args.invoice_id else None,
                "total_cost":args.total_cost if args.total_cost else None,
                "paid_cost":args.paid_cost if args.paid_cost else None,
                "balance_cost":args.balance_cost if args.balance_cost else None,
                "payment_status":args.payment_status if args.payment_status else None,
             }

    data = cc.reports.update_invoice(**kwargs)
    utils.process_updated_values(data)

@utils.arg('-v', '--invoice-id',
           help='invoice_id',
           required=False)
def do_invoice_delete(cc, args):
    """ delete invoice details."""

    # invoice arguments
    kwargs = {
                "invoice_id":args.invoice_id if args.invoice_id else None,
             }

    data = cc.reports.delete_invoice(**kwargs)
