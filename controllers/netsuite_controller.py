import threading
from io import BytesIO
import io
import pandas as pd
import os
import numpy as np

from constants.crm_table_constants import crm_table_with_optional_values
from constants.rialto_table_constants import rialto_table_fields_with_optional_values
from constants.ship_method import cds_entity_to_subsidiary, subsidiary_to_ship_method
from database import get_db
from helper_file import download_from_azure, OUTPUT_DIRECTORY_NAME, ERROR_DIRECTORY_NAME, update_fields_db, \
    CONFIG_DIRECTORY_NAME
from model.contract import Contract, contract_model_columns

from services.mail_service import mail_file
from helper_file import upload_to_azure


def check_account_exist(field_name, customer_id, account_file_df):
    try:
        print(f"Here is the check account field {field_name}:::; {customer_id}")
        matching_rows = account_file_df[account_file_df['Accounts'] == customer_id]
        if len(matching_rows) == 0:
            raise KeyError(f"Customer could not be found in the Account file.  {field_name}")
    except KeyError as e:
        print(f"Missing key '{e}' in the input row.")
        raise ValueError(f"Missing key '{e}' in the input row.")


def get_data_bill_to_end_user_field(field_name, cnt_number, df, account_file_df, errors):
    bill_to_end_user_field = None
    try:
        matching_rows = df[df['CNT Number'] == cnt_number]
        if len(matching_rows) == 0:
            raise KeyError(f"CNT Number not found in the Bill_to_end_user file for column {field_name}")
        bill_to_end_user_fields = matching_rows[f'{field_name}'].tolist()
        bill_to_end_user_field = bill_to_end_user_fields[0]
        if bill_to_end_user_field is None or (
                isinstance(bill_to_end_user_field, str) and bill_to_end_user_field.strip() == "") or pd.isna(
                bill_to_end_user_field):
            raise KeyError(
                f"The field '{field_name}' is empty in the in table bill_to_end_user for cnt number : {cnt_number} .")
        if field_name in ['Bill To Addressee External ID', 'End User External ID']:
            check_account_exist(field_name, bill_to_end_user_field, account_file_df)
        return bill_to_end_user_field, errors
    except KeyError as e:
        print(f"Missing key '{e}' in the input row.")
        errors.append(f"Missing key '{e}' in the input row.")
        return bill_to_end_user_field, errors


def get_crm_data_field(field_name, cnt_number, df):
    try:
        matching_rows = df[df['Contract Number'] == cnt_number]
        if len(matching_rows) == 0:
            raise KeyError("CNT Number could not be found in the CRM data file.")
        crm_response_fields = matching_rows[f'{field_name}'].tolist()
        crm_response_field = crm_response_fields[0]
        if field_name in crm_table_with_optional_values and pd.isna(crm_response_field):
            return ""
        if crm_response_field is None or (
                isinstance(crm_response_field, str) and crm_response_field.strip() == "") or pd.isna(
            crm_response_field):
            raise KeyError(
                f"The field '{field_name}' is empty in the in table CRM data for cnt number : {cnt_number} .")
        return crm_response_field
    except KeyError as e:
        print(f"Missing key '{e}' in the input row.")
        raise ValueError(f"Missing key '{e}' in the input row.")


def get_contract_months(coverage_start_date, coverage_end_date, errors):
    try:
        months_difference = (coverage_end_date.year - coverage_start_date.year) * 12 + (
                coverage_end_date.month - coverage_start_date.month)

        if (coverage_end_date - (coverage_start_date + pd.DateOffset(months=months_difference))).days >= 27:
            months_difference += 1

    except Exception as e:
        print(f"An error occurred while calculating contract months: {e}")
        errors.append(f"Missing key or exception'{e}' in the input row.")
        return 0, errors

    return months_difference, errors


def get_contract_rate(extended_price, coverage_start_date, coverage_end_date, billing_frequency, errors):
    try:
        if extended_price == "":
            extended_price = 0
        print(f"extended price: {extended_price},,,coverage_start and end {coverage_end_date}, {coverage_start_date}")
        match billing_frequency[0]:
            case "Quarterly":
                return 3 * extended_price, errors
            case "Annually":
                return 12 * extended_price, errors
            case "Paid-In-Full":
                months_difference = (coverage_end_date.year - coverage_start_date.year) * 12 + (
                        coverage_end_date.month - coverage_start_date.month)
                if (coverage_end_date - (coverage_start_date + pd.DateOffset(months=months_difference))).days >= 27:
                    months_difference += 1
                return months_difference * extended_price, errors
            case _:
                return extended_price, errors
    except Exception as e:
        errors.append(f"Missing key or exception '{e}' in the input row.")
        return 0, errors


def get_item_line_sales_price(extended_price, billing_frequency, errors):
    try:
        if extended_price == "":
            extended_price = 0
        match billing_frequency:
            case "Quarterly":
                return 3 * extended_price, errors
            case "Annually" | "Paid-In-Full":
                return 12 * extended_price, errors
            case _:
                return extended_price, errors

    except Exception as e:
        errors.append(f"Errors found while extended price {e}")
        return 0, errors


def get_ship_postalcode(country, postal_code, errors):
    try:
        if country == 'United States':

            if len(postal_code) < 5:
                postal_code = postal_code.zfill(5)

            return postal_code, errors

        return str(postal_code), errors

    except KeyError as e:
        print(f"Error: Missing key {e} in the input row.")
        errors.append(f"Missing key {e} in the input row.")
        return "", errors


def get_subsidiary(cds_entity):
    if cds_entity in cds_entity_to_subsidiary:
        return cds_entity_to_subsidiary[cds_entity]
    else:
        raise ValueError(f"Entity '{cds_entity}' not found in subsidiary")


def get_ship_method_from_subsidiary(subsidiary):
    if subsidiary in subsidiary_to_ship_method:
        return subsidiary_to_ship_method[subsidiary]
    else:
        raise ValueError(f"Subsidiary '{subsidiary}' not found in subsidiary_to_ship_method")


def get_ship_method(cds_entity):
    try:
        subsidiary_id = get_subsidiary(cds_entity)
        ship_method = get_ship_method_from_subsidiary(subsidiary_id)
        return str(ship_method)
    except KeyError as e:
        print(f"Missing key '{e}' in the input row.")
        raise ValueError(f"Missing key '{e}' in the input row.")


def get_rialto_field(row, field_name):
    try:
        value = row[field_name]
        if value is None or (isinstance(value, str) and value.strip() == "") or pd.isna(value):
            if field_name in rialto_table_fields_with_optional_values and pd.isna(value):
                return ""
            raise KeyError(f"The field '{field_name}' is empty in the input row.")
        if field_name == 'Serial Number' and isinstance(value, int):
            return str(value)
        return value

    except KeyError as e:
        print(f"Missing key '{e}' in the input row.")
        raise ValueError(f"Missing key '{e}' in the input row.")


def check_data_from_golden_list(golden_list_df, device_type, manufacturer, item_model, errors):
    if golden_list_df.empty:
        raise ValueError("The golden list DataFrame is empty.")

    manufacturer_condition = 'hpe' if manufacturer.lower() == 'hp' else manufacturer.lower()

    filtered_df = golden_list_df[
        (golden_list_df['Device Type'].str.strip().str.lower() == device_type.strip().lower()) &
        (golden_list_df['Manufacturer'].str.strip().str.lower() == manufacturer_condition) &
        (golden_list_df['Model'].str.strip().str.lower() == item_model.strip().lower())
        ]

    if not filtered_df.empty:
        return errors
    else:
        errors.append(
            f"No matching record found in the golden list for Device Type: {device_type}, Manufacturer: {manufacturer} and Model :{item_model}")
        return errors


def process_row(row, bill_to_end_user_df, netsuite_crm_df, account_df, golden_list_df):
    errors = []
    try:
        print("code is in process row")
        cnt_number = get_rialto_field(row, 'CNT Number')
        coverage_start_date_value = get_rialto_field(row, 'Coverage Start Date')
        coverage_end_date_value = get_rialto_field(row, 'Coverage End Date')
        extended_price = get_rialto_field(row, 'Extended Price')
        postal_code = str(get_rialto_field(row, 'Postal Code'))
        country = get_rialto_field(row, 'Country')
        device_type = get_rialto_field(row, 'Device Type')
        manufacturer = get_rialto_field(row, 'Manufacturer')
        item_model = get_rialto_field(row, 'Model or Part Number')
        coverage_sla = get_rialto_field(row, 'Coverage SLA ')
        support_level = get_rialto_field(row, 'Support Level')

        cds_entity = get_crm_data_field('CDS Entity', cnt_number, netsuite_crm_df)
        sales_rep_contract_id = get_crm_data_field('Owner', cnt_number, netsuite_crm_df)
        po_number = get_crm_data_field('PO Number', cnt_number, netsuite_crm_df)
        customer_ref_number = get_crm_data_field('CustRefNumb', cnt_number, netsuite_crm_df)
        billing_frequency = get_crm_data_field('Billing Frequency', cnt_number, netsuite_crm_df)
        net_terms = get_crm_data_field('Net Terms', cnt_number, netsuite_crm_df)
        currency = get_crm_data_field('Currency', cnt_number, netsuite_crm_df)

        customer_acc_contract_id, errors = get_data_bill_to_end_user_field('Bill To Addressee External ID', cnt_number,
                                                                           bill_to_end_user_df, account_df, errors)
        end_user_external_id, errors = get_data_bill_to_end_user_field('End User External ID', cnt_number,
                                                                       bill_to_end_user_df,
                                                                       account_df, errors)

        coverage_start_date = pd.to_datetime(coverage_start_date_value) if coverage_start_date_value else pd.Timestamp(
            '1900-01-01')
        coverage_end_date = pd.to_datetime(coverage_end_date_value) if coverage_end_date_value else pd.Timestamp(
            '1900-01-01')

        sales_price, errors = get_item_line_sales_price(extended_price, billing_frequency, errors)
        contract_rate, errors = get_contract_rate(extended_price, coverage_start_date, coverage_end_date,
                                                  billing_frequency, errors)
        contract_months, errors = get_contract_months(coverage_start_date, coverage_end_date, errors)
        postal_code, errors = get_ship_postalcode(country, postal_code, errors)
        mm_dd_yyyy_format = '%m/%d/%Y'

        errors = check_data_from_golden_list(golden_list_df, device_type, manufacturer, item_model, errors)
        # errors = check_data_from_golden_list(golden_list_df, device_type, manufacturer, item_model, coverage_sla,
        #                                      support_level, errors)  #checking data from golden list

        contract_row = Contract(
            externalid=cnt_number,
            Customer=customer_acc_contract_id,
            subsidiary=cds_entity,
            orderstatus="Pending Approval",
            salesrep=sales_rep_contract_id,
            otherrefnum=po_number,
            custbody_rr_startnewcontract='TRUE',
            custbody_rr_contract="",
            memo="",
            ismultishipto="TRUE",
            custbody_360_cus_refnum=customer_ref_number,
            itemLine_item=93,
            itemLine_quantity=1,
            itemLine_salesPrice=sales_price,
            custcol_rr_contractrate=contract_rate,
            itemLine_pricelevel="Custom",
            itemLine_description="Contract maintenance",
            custcol_rr_assetnumber=get_rialto_field(row, 'Serial Number'),
            custcol_rr_contracttermmonths=contract_months,
            custcol_rr_contractbillingfreq=billing_frequency,
            custcol_rr_enduser=end_user_external_id,
            itemLine_department="",
            itemLine_class="",
            itemLine_location="",
            custcol_rr_startdate=pd.to_datetime(coverage_start_date).strftime(mm_dd_yyyy_format),
            custcol_rr_enddate=pd.to_datetime(coverage_end_date).strftime(mm_dd_yyyy_format),
            custcol_360_original_start_date=pd.to_datetime(coverage_start_date).strftime(mm_dd_yyyy_format),
            custcol_rr_intitalbilling="",
            custcol_rr_contractlineforcoterming="",
            cseg_device_type=device_type,  #have to add validation
            cseg_manufacturer=manufacturer,  #have to add validation
            cseg_360_item_model=item_model,  #have to add validation
            cseg_service_offr=coverage_sla,  #have to add validation
            cseg_support_type=support_level,  #have to add validation
            cseg_service_tier="Standard",
            custcol_360_part_subcontractor="",
            custcol_360_line_po="",
            shipcarrier="",
            shipmethod=get_ship_method(cds_entity),
            shipaddressee="",
            shipAddr1=get_rialto_field(row, 'Address 1'),
            shipAddr2=get_rialto_field(row, 'Address 2'),
            shipAddr3=get_rialto_field(row, 'Address 3'),
            shipCity=get_rialto_field(row, 'City'),
            shipState=get_rialto_field(row, 'State/Province'),
            shipZip=postal_code,
            shipCountry=get_rialto_field(row, 'Country'),
            terms=net_terms,
            billAddressee="",
            billAddr1="",
            billAddr2="",
            billCity="",
            billState="",
            billZip="",
            billCountry="",
            currency=currency
        )
        print(f"code in process row {contract_row}")
        if len(errors) != 0:
            raise ValueError(f"Here the error {errors}")
        return contract_row
    except Exception as e:
        error_message = f"Error processing row : {e}"
        print(error_message)
        raise ValueError(error_message)


def get_data_for_df(correct_data):
    data = [{
        'externalid': contract.externalid,
        'Customer': contract.Customer,
        'subsidiary': contract.subsidiary,
        'orderstatus': contract.orderstatus,
        'salesrep': contract.salesrep,
        'otherrefnum': contract.otherrefnum,
        'custbody_rr_startnewcontract': contract.custbody_rr_startnewcontract,
        'custbody_rr_contract': contract.custbody_rr_contract,
        'memo': contract.memo,
        'ismultishipto': contract.ismultishipto,
        'custbody_360_cus_refnum': contract.custbody_360_cus_refnum,
        'itemLine_item': contract.itemLine_item,
        'itemLine_quantity': contract.itemLine_quantity,
        'itemLine_salesPrice': contract.itemLine_salesPrice,
        'custcol_rr_contractrate': contract.custcol_rr_contractrate,
        'itemLine_pricelevel': contract.itemLine_pricelevel,
        'itemLine_description': contract.itemLine_description,
        'custcol_rr_assetnumber': contract.custcol_rr_assetnumber,
        'custcol_rr_contracttermmonths': contract.custcol_rr_contracttermmonths,
        'custcol_rr_contractbillingfreq': contract.custcol_rr_contractbillingfreq,
        'custcol_rr_enduser': contract.custcol_rr_enduser,
        'itemLine_department': contract.itemLine_department,
        'itemLine_class': contract.itemLine_class,
        'itemLine_location': contract.itemLine_location,
        'custcol_rr_startdate': contract.custcol_rr_startdate,
        'custcol_rr_enddate': contract.custcol_rr_enddate,
        'custcol_360_original_start_date': contract.custcol_360_original_start_date,
        'custcol_rr_intitalbilling': contract.custcol_rr_intitalbilling,
        'custcol_rr_contractlineforcoterming': contract.custcol_rr_contractlineforcoterming,
        'cseg_device_type': contract.cseg_device_type,
        'cseg_manufacturer': contract.cseg_manufacturer,
        'cseg_360_item_model': contract.cseg_360_item_model,
        'cseg_service_offr': contract.cseg_service_offr,
        'cseg_support_type': contract.cseg_support_type,
        'cseg_service_tier': contract.cseg_service_tier,
        'custcol_360_part_subcontractor': contract.custcol_360_part_subcontractor,
        'custcol_360_line_po': contract.custcol_360_line_po,
        'shipcarrier': contract.shipcarrier,
        'shipmethod': contract.shipmethod,
        'shipaddressee': contract.shipaddressee,
        'shipAddr1': contract.shipAddr1,
        'shipAddr2': contract.shipAddr2,
        'shipAddr3': contract.shipAddr3,
        'shipCity': contract.shipCity,
        'shipState': contract.shipState,
        'shipZip': contract.shipZip,
        'shipCountry': contract.shipCountry,
        'terms': contract.terms,
        'billAddressee': contract.billAddressee,
        'billAddr1': contract.billAddr1,
        'billAddr2': contract.billAddr2,
        'billCity': contract.billCity,
        'billState': contract.billState,
        'billZip': contract.billZip,
        'billCountry': contract.billCountry,
        'currency': contract.currency
    } for contract in correct_data]

    return data


def save_dataframe_as_csv(dataframe, file_name):
    directory = os.getenv('EXCEL_FILES_DIRECTORY')

    file_path = os.path.join(os.path.dirname(__file__), directory, file_name)

    dataframe.to_csv(file_path, index=False)
    csv_buffer = io.StringIO()
    dataframe.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    return file_path, csv_bytes


def handle_incorrect_data(incorrect_data, file_name, new_upload):
    incorrect_data_df = pd.DataFrame(incorrect_data)
    incorrect_file_name = f"Incorrect_{file_name.split('.')[0]}.csv"
    incorrect_data_filepath, incorrect_file_data = save_dataframe_as_csv(incorrect_data_df, incorrect_file_name)
    mail_file(incorrect_data_filepath, "failed")
    print('Mailed Failed File ')
    azure_file_path = f"{ERROR_DIRECTORY_NAME}/{incorrect_file_name}"
    upload_to_azure(azure_file_path, incorrect_file_data)
    update_fields_db(new_upload, azure_file_path, "failed")
    remove_file_from_temp_folder(incorrect_data_filepath)


def get_aggregation(correct_data_df):
    agg_df = correct_data_df.groupby(
        ['externalid', 'Customer', 'itemLine_salesPrice', 'custcol_rr_contractbillingfreq',
         'custcol_rr_enduser', 'custcol_rr_enddate', 'custcol_rr_startdate',
         'cseg_device_type', 'cseg_manufacturer', 'cseg_360_item_model',
         'cseg_service_offr', 'cseg_support_type', 'custcol_360_part_subcontractor',
         'shipaddressee', 'shipAddr1', 'shipAddr2', 'shipAddr3',
         'billCity', 'billState', 'billZip']
    ).agg(
        custcol_rr_assetnumber=('custcol_rr_assetnumber', lambda x: '\n'.join(x)),
        itemLine_quantity=('itemLine_quantity', 'sum'),
        subsidiary=('subsidiary', 'first'),
        orderstatus=('orderstatus', 'first'),
        salesrep=('salesrep', 'first'),
        otherrefnum=('otherrefnum', 'first'),
        custbody_rr_startnewcontract=('custbody_rr_startnewcontract', 'first'),
        custbody_rr_contract=('custbody_rr_contract', 'first'),
        memo=('memo', 'first'),
        ismultishipto=('ismultishipto', 'first'),
        custbody_360_cus_refnum=('custbody_360_cus_refnum', 'first'),
        itemLine_item=('itemLine_item', 'first'),
        custcol_rr_contractrate=('custcol_rr_contractrate', 'first'),
        itemLine_pricelevel=('itemLine_pricelevel', 'first'),
        itemLine_description=('itemLine_description', 'first'),
        custcol_rr_contracttermmonths=('custcol_rr_contracttermmonths', 'first'),
        itemLine_department=('itemLine_department', 'first'),
        itemLine_class=('itemLine_class', 'first'),
        itemLine_location=('itemLine_location', 'first'),
        custcol_360_original_start_date=('custcol_360_original_start_date', 'first'),
        custcol_rr_intitalbilling=('custcol_rr_intitalbilling', 'first'),
        custcol_rr_contractlineforcoterming=('custcol_rr_contractlineforcoterming', 'first'),
        cseg_service_tier=('cseg_service_tier', 'first'),
        custcol_360_line_po=('custcol_360_line_po', 'first'),
        shipcarrier=('shipcarrier', 'first'),
        shipmethod=('shipmethod', 'first'),
        shipCity=('shipCity', 'first'),
        shipState=('shipState', 'first'),
        shipZip=('shipZip', 'first'),
        shipCountry=('shipCountry', 'first'),
        terms=('terms', 'first'),
        billAddressee=('billAddressee', 'first'),
        billAddr1=('billAddr1', 'first'),
        billAddr2=('billAddr2', 'first'),
        billCountry=('billCountry', 'first'),
        currency=('currency', 'first')
    ).reset_index()
    # Step 2: Handle splitting of rows if custcol_rr_assetnumber length >= 4000
    final_rows = []

    for _, row in agg_df.iterrows():
        asset_numbers = row['custcol_rr_assetnumber'].split('\n')
        total_quantity = row['itemLine_quantity']

        # Initialize variables for splitting
        current_asset_number = ''
        current_quantity = 0

        for asset_number in asset_numbers:
            if len(current_asset_number) + len(asset_number) + 1 < 4000:  # +1 for newline
                if current_asset_number:
                    current_asset_number += '\n'
                current_asset_number += asset_number
                current_quantity += total_quantity // len(asset_numbers)  # Distributing quantity
            else:
                # Append the current row to final_rows
                final_rows.append({
                    **row.to_dict(),
                    'custcol_rr_assetnumber': current_asset_number,
                    'itemLine_quantity': current_quantity
                })
                # Reset for the next row
                current_asset_number = asset_number
                current_quantity = total_quantity // len(asset_numbers)  # Start new row with current asset number

        # Append the last accumulated row if it exists
        if current_asset_number:
            final_rows.append({
                **row.to_dict(),
                'custcol_rr_assetnumber': current_asset_number,
                'itemLine_quantity': current_quantity
            })

    # Create a DataFrame from the final rows
    final_df = pd.DataFrame(final_rows)

    return final_df


def remove_file_from_temp_folder(file_path):
    os.remove(file_path)
    print(f"File has been deleted {file_path}")


def handle_correct_data(correct_data, file_name, new_upload):
    data_for_df = get_data_for_df(correct_data)
    correct_data_df = pd.DataFrame(data_for_df)
    correct_aggregated_filename = f"Correct_{file_name.split('.')[0]}.csv"
    corrected_aggregated_df = get_aggregation(correct_data_df)
    corrected_aggregated_df = corrected_aggregated_df[contract_model_columns]
    correct_aggregated_data_filepath, correct_file_data = save_dataframe_as_csv(corrected_aggregated_df,
                                                                                correct_aggregated_filename)
    mail_file(correct_aggregated_data_filepath, "passed")
    print('Mailed Correct File ')
    azure_file_path = f"{OUTPUT_DIRECTORY_NAME}/{correct_aggregated_filename}"
    upload_to_azure(azure_file_path, correct_file_data)
    update_fields_db(new_upload, azure_file_path, "success")
    remove_file_from_temp_folder(correct_aggregated_data_filepath)


def build_data_netsuite(file_name, dataframe, new_upload):
    print("code is in the netsuite code")
    correct_data = []
    incorrect_data = []
    netsuite_crm_migration_file = download_from_azure(
        f"{CONFIG_DIRECTORY_NAME}/{os.getenv('NETSUITE_MIGRATION_CRM_FILE')}")
    bill_to_end_user_file = download_from_azure(f"{CONFIG_DIRECTORY_NAME}/{os.getenv('BILL_TO_END_USER_FILE')}")
    account_file = download_from_azure(f"{CONFIG_DIRECTORY_NAME}/{os.getenv('ACCOUNT_FILE')}")
    golden_list_file = download_from_azure(f"{CONFIG_DIRECTORY_NAME}/{os.getenv('GOLDEN_LIST')}")

    account_df = pd.read_excel(account_file)
    bill_to_end_user_df = pd.read_excel(bill_to_end_user_file)
    netsuite_crm_df = pd.read_excel(netsuite_crm_migration_file)
    golden_list_df = pd.read_excel(golden_list_file)
    print("file is being uploaded")
    for index, row in dataframe.iterrows():
        print(f"Print Row Number {index}")
        try:
            netsuite_row = process_row(row.to_dict(), bill_to_end_user_df, netsuite_crm_df, account_df, golden_list_df)
            # If successful, add to correct_data
            correct_data.append(netsuite_row)
        except Exception as e:
            # If an error occurs, add the row and error message to incorrect_data
            print(f'Error processing row {index}: {str(e)}')
            incorrect_data.append({
                "serial_number": row["Serial Number"],
                "row_data": row.to_dict(),
                "error": str(e)
            })
    if len(incorrect_data) != 0:
        handle_incorrect_data(incorrect_data, file_name, new_upload)
    else:
        handle_correct_data(correct_data, file_name, new_upload)
    print(f"here is the incorrect data {incorrect_data}")


async def process_action(file_path, file_data, new_upload):
    try:
        print("code still in process action")
        file_name = file_path.split('/')[-1]
        excel_file = BytesIO(file_data)
        df = pd.read_excel(excel_file, header=1)
        t1 = threading.Thread(target=build_data_netsuite, args=(file_name, df, new_upload))
        t1.start()
    except Exception as e:
        print(f"Something went wrong while uploading data due to error {e}")
