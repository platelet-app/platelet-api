from app.cloud import AwsStore


class CloudStores:
    def __init__(self, platform, profile_picture_store_name, region, access_key_id, secret_access_key_id, endpoint):
        self.platform = platform
        self.profile_picture_store = None
        self.profile_picture_store_name = profile_picture_store_name
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key_id = secret_access_key_id
        self.endpoint = endpoint

    def initialise_profile_pictures_store(self):
        if self.platform == "aws":
            self.profile_picture_store = AwsStore(
                bucket_name=self.profile_picture_store_name,
                region=self.region,
                access_key_id=self.access_key_id,
                secret_access_key_id=self.secret_access_key_id,
                endpoint=self.endpoint
            )

    def get_profile_picture_store(self):
        return self.profile_picture_store
