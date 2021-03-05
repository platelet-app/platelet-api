import csv
import logging


def get_mailing_list():
    try:
        with open("/tmp/mailing_list.csv") as mailing_list:
            return mailing_list.read().split(",")
    except FileNotFoundError:
        logging.warning("Mailing list file not found, attempting download from bucket.")
        from app import cloud_stores
        cloud_stores.initialise_mailing_list_store()
        store = cloud_stores.get_mailing_list_store()
        list_obj = store.get_object("mailing_list.csv")
        list_obj.download_file("/tmp/mailing_list.csv")

    with open("/tmp/mailing_list.csv") as mailing_list:
        return mailing_list.read().split(",")


def upload_mailing_list(updated_list):
    with open("/tmp/mailing_list.csv", 'w') as mailing_list:
        csv = ",".join(updated_list)
        mailing_list.write(csv)

    from app import cloud_stores
    cloud_stores.initialise_mailing_list_store()
    store = cloud_stores.get_mailing_list_store()
    list_obj = store.get_object("mailing_list.csv")
    logging.info(dir(list_obj))
    list_obj.upload_file("/tmp/mailing_list.csv")
