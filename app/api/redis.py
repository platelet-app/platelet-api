from rq.job import Job

from app import root_ns as ns
from redis_worker import conn
from flask_restx import Resource

@ns.route("/results/<job_key>", endpoint="redis_queries")
class Redis(Resource):
    def get(self, job_key):
        job = Job.fetch(job_key, connection=conn)
        if job.is_finished:
            return {"message": str(job.result)}, 200
        else:
            return {"message": "pending"}, 202
