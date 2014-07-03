import os
import warnings

import boto.sns


class SNSAlert:
    @staticmethod
    def prepare(region, topic):
        alert = SNSAlert()
        try:
            if alert.load_creds() is False:
                raise Exception('File not found')
        except Exception as e:
            warnings.warn('No SNS credentials found in config/iamcreds.conf: {}'.format(e))
            return False

        alert.conn = boto.sns.connect_to_region(
            region,
            aws_access_key_id=alert.access_id,
            aws_secret_access_key=alert.secret_key,
        )
        alert.topic = topic
        return alert

    def load_creds(self):
        if not os.path.exists('config/iamcreds.conf'):
            return False

        # read and parse the IAM config file
        with open('config/iamcreds.conf', 'r') as f:
            for line in f.read().splitlines():
                if 'access_id' in line:
                    self.access_id = line.split('=')[1]
                if 'secret_key' in line:
                    self.secret_key = line.split('=')[1]

        return True

    def send(self, message, subject=None):
        print 'SNSAlert: {0}'.format(message)
        self.conn.publish(self.topic, message, subject)
