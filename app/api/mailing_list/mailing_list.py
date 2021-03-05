from app import mailing_list_ns as ns
from flask_restx import Resource, reqparse
from app.api.functions.errors import bad_request_error
from app.api.mailing_list.mailing_list_utilities.mailing_list_functions import get_mailing_list, upload_mailing_list
from app import flask_praetorian
import logging


@ns.route('')
class MailingList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email_address", type=str)
        args = parser.parse_args()
        logging.info(args)
        logging.info(args['email_address'])
        if not args['email_address']:
            return bad_request_error("An email address was not sent.")
        mailing_list = get_mailing_list()
        mailing_list.append(args['email_address'])
        set_dedup = set(mailing_list)
        upload_mailing_list(list(set_dedup))

        return {"message": "Mailing list updated"}, 201

    @flask_praetorian.roles_accepted("admin")
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email_address", type=str)
        args = parser.parse_args()
        if not args['email_address']:
            return bad_request_error("An email address was not in the input data.")
        email_address = args['email_address']

        mailing_list = get_mailing_list()
        result = filter(lambda e: e != email_address, mailing_list)
        upload_mailing_list(result)

        return {"message": "Mailing list updated"}, 202
