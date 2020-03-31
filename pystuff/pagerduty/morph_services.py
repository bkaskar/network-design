from datetime import datetime
import json
import os
import sys
import requests
import logging
import env.settings
from pdrest import PagerDutyREST

""" fixme - get logging fixed and move to config """
logger = logging.getLogger(__name__)

class CreateRenamedSvcs(): 
    def __init__(self, access_token):
        self.pd_rest = PagerDutyREST(access_token)

    def util_repl_none_null_in_dict(self, a_dict, del_keys):
        """ Given a set of keys, remove them from given payload """
        new_dict = {}
        if isinstance(a_dict, dict):
            for k, v in a_dict.items():
                cache = []
                if k not in del_keys:
                    if isinstance(v, dict):
                        cache = self.util_repl_none_null_in_dict(v, del_keys)
                        new_dict[k] = cache
                    elif isinstance(v, list):
                        for n, item in enumerate(v):
                            cache.append(self.util_repl_none_null_in_dict(item, del_keys))
                        new_dict[k] = cache
                    elif k in del_keys :
                        continue
                    elif v is None :
                        v = '[]'
                        continue
                    else :
                        new_dict[k] = v
                continue

        return new_dict

    def getExactObjectID(self, list_cache, item_type, item_name):
        """ old unused method to find an attribute """
        if isinstance(list_cache, list):
            # has multiples of given item_type
            for list_item in list_cache:
                print(list_item)

        if isinstance(list_cache, dict):
            pass
        with open (file_handle) as json_file:
            data = json.load(json_file)
            l1_attr_count = len(data[item_type])
            l1_attrs = data[item_type]
            attributeID = ""
            if l1_attr_count > 1:
                for single_obj in l1_attrs:
                    for k, v in single_obj.items():
                        if str(v) == item_name:
                            if attributeID != single_obj['id']:
                                attributeID = single_obj['id']
                        elif l1_attr_count == 1:
                            single_obj = l1_attrs[0]
                            attributeID = single_obj['id']
                        else:
                            attributeID = "NOT FOUND"
                print(attributeID)

    def get_integration_by_id(self, service_id, integration_id):
        r = self.pd_rest.get('/services/{id}/integrations/{int_id}'.format(
            int_id=integration_id,
            id=service_id
        ))
        return r['integration']
        
        raise ValueError(
            'Integration {int_id} is not attached to services {id}'.format(
                int_id=integration_id,
                id=service_id
            )
        )

    def get_team_services(self, team_id, svcs_like):
        """" return set of service(s) like svcs_like for a team """"

        r = self.pd_rest.get('/services', 
            {
                'query': svcs_like,
                'team_ids[]': team_id,
                'time_zone': 'UTC',
                'sort_by': 'name'
            },
            'services'
        )
        
        if len(r['services']) > 0:
            # print('Total {num} services found for this team'.format(num=len(r['services'])))
            return r['services']
            
        raise ValueError(
            'There are no services in {team}'.format(team=team_id)
        )
   
    def get_team_id(self, team_name):
        
        r = self.pd_rest.get('/teams', {'query': team_name})
        if len(r['teams']) > 0:
            for team in r['teams']:
                if str(team['name']).lower().strip() == team_name.lower().strip():
                    return team['id']
        raise ValueError(
            'Could not find reqeusted {team}'.format(team=team_name)
        )

    def list_open_incidents(self, user_id=None, service_id=None, team_id=None):
        """Get any open incidents assigned to the user"""

        payload = { 'total': True, 'statuses[]': ['triggered', 'acknowledged'], 'time_zone': 'UTC' }

        if user_id is not None:
            payload['user_ids[]'] = user_id
        if service_id is not None:
            payload['service_ids[]'] = service_id
        if team_id is not None:
            payload['team_ids[]'] = team_id

        r = self.pd_rest.get('/incidents', payload, 'incidents')
        return r

    def resolve_incidents(self, incidents, from_email):
        """Resolves all incidents"""
        
        for incident in incidents:
            logger.info('Resolving {id}'.format(id=incident))
            try:
                self.resolve_open_incident(incident, from_email)
            except:
                logger.error(
                    'Could not resolve incident {id}'.format(id=incident)
                )

    def resolve_open_incident(self, incident_id, from_email):
        """Resolves an incident"""

        payload = {
            'incident': {
                'type': 'incident_reference',
                'resolution': 'FORCED RESOLUTION IN-COMPLIANCE TO W3ID DEACTIVATION.',
                'status': 'resolved'
            }
        }
        r = self.pd_rest.put(
            '/incidents/{id}'.format(id=incident_id),
            payload,
            from_email
        )
        return r

    def new_email_integration(self, integration_dict):
        discard_key_pile = (
            'id',
            'service',
            'created_at',
            'vendor',
            'self',
            'html_url'
        )

        new_integration = { "integration": self.util_repl_none_null_in_dict(integration_dict, discard_key_pile)}

        # new_integration = self.util_repl_none_null_in_dict(new_integration)
        # str_int = json.dumps(new_integration, indent=2)
        # new_integration = 

        return new_integration

    def delete_service_by_id(self, service_id):
        call_delete = '/services/{id}'.format(id=service_id)
        r = self.pd_rest.delete(call_delete)

    def delete_services(self, services):
        for service in services:
            incidents = self.list_open_incidents(service['id'],service['teams'][0]['id'])
            self.resolve_incidents(incidents, 'pagerduty@us.ibm.com')
            self.delete_service_by_id(service['id'])

    def create_new_service(self, service_dict):
        new_service_integrations = []

        if len(service_dict['integrations']) > 0:
            """ get email integrations """
            for integration in service_dict['integrations']: 

                old_integration = self.get_integration_by_id(service_dict['id'],integration['id'])

                email = old_integration['integration_email'].lower().replace('blue', 'red')
                old_integration['integration_email'] = email
                new_integration = self.new_email_integration(old_integration)
                new_service_integrations.append(new_integration)
        
        new_service = { "service": 
            { k:v 
            for k, v in service_dict.items() 
                if k not in (
                    'id',
                    'integrations',
                    'created_at',
                    'updated_at',
                    'last_incident_timestamp',
                    'self',
                    'html_url'
                )
            } 
        }


        r = self.pd_rest.post('/services', new_service)

        # print('At this point integration\n{inte}\n can be added to \n{svc}'.format(inte=json.dumps(new_int, indent=2), svc=json.dumps(r['service'], indent=2)))

        new_service_id = r['service']['id']
        for new_int in new_service_integrations:
           i = self.pd_rest.post('/services/{id}/integrations'.format(id=new_service_id),new_int)
        quit()
    


def main():
    token = env.settings.pd_write
    copy_svc = CreateRenamedSvcs(token)

    team_id = copy_svc.get_team_id('a specific pd team')

    services = copy_svc.get_team_services(team_id, 'service name containing this string')

    # Use this for cleanup only!!
    # services = copy_svc.get_team_services(team_id, 'Redcode')
    # copy_svc.delete_services(services)

    for service in services:
        name = service['name'].replace('Blue', 'Red')
        service['name'] = name
        service['summary'] = name
        try:
            copy_svc.create_new_service(service)
        except Exception as error:
            print(error)
        continue


if __name__ == "__main__":
    main()

