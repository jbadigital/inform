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
            'monitoring.status',
            expr_form='compound',
            timeout=20
        )
        if not results:
            alert = SNSAlert.prepare(ec2_region, self.sns_topic)
            if alert:
                alert.send(
                    'No data retrieved via Salt in {}'.format(ec2_region),
                    'Boomerang Notifications Failure'
                )
            return {}

        for client_ref, data in results[results.keys()[0]].items():
            if client_ref in ('www_optus_com_au', 'virginmobile_com_au'):
                # raise an alert if 2 hour sends is zero
                if data['sends_last_2hrs'] == 0:
                    self.alert(client_ref, 2)

            elif client_ref in ('goodlifehealthclubs_com_au', 'melbourneit_com_au'):
                # raise an alert if 4 hour sends is zero
                if data['sends_last_4hrs'] == 0:
                    self.alert(client_ref, 4)

            # store raw metrics
            output[client_ref] = {'timestamp': datetime.datetime.now().isoformat()}
            for key, value in data.items():
                output[client_ref][key] = value

                # log everything to graphite
                #if key != "timestamp":
                #    self.log_to_graphite("clients.{}.{}".format(client_ref, key), value)

        return output

    def alert(self, client_ref, hours):
        alert = SNSAlert.prepare(ec2_region, self.sns_topic)
        if alert:
            alert.send(
                ('Boomerang sends are zero for the last {} hours for {}\n\n'
                 'http://monitor.au.basketchaser.com').format(hours, client_ref),
                'Boomerang Send Warning for {}'.format(client_ref)
            )
