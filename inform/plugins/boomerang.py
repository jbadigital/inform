from ..base_plugins import InformBasePlugin

from ..alerts.sns import SNSAlert

import datetime

import salt

try:
    # load current EC2 region at start up
    caller = salt.client.Caller()
    ec2_region = caller.function('grains.item', 'ec2_region')['ec2_region']
except:
    print "Couldn\'t load EC2 region via Salt grains!"


class MonitorPlugin(InformBasePlugin):
    run_every = datetime.timedelta(minutes=30)
    plugin_name = 'boomerang'
    sort_output = True

    sns_topic = 'arn:aws:sns:ap-southeast-2:977487671053:boomerang-no-sends'

    def process(self):
        output = {}

        # query boomerang stats via custom salt module
        client = salt.client.LocalClient()
        results = client.cmd(
            'G@ec2_region:{} and G@role:rabbit'.format(ec2_region),
            'monitoring.client_status',
            expr_form='compound'
        )

        for client_ref, data in results[results.keys()[0]].items():
            # raise an alert if 2 hour sends is zero
            if data['sends_last_2hrs'] == 0:
                alert = SNSAlert.prepare(ec2_region, self.access_id, self.secret_key, self.sns_topic)
                alert.send(
                    'Boomerang sends are zero for the last 2 hours for {0}'.format(client_ref),
                    'Boomerang Send Warning for {0}'.format(client_ref)
                )

            # store raw metrics
            output[client_ref] = {'timestamp': datetime.datetime.now().isoformat()}
            for key, value in data.items():
                output[client_ref][key] = value

        return output
