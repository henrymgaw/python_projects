{# Syntax #}

{#

salt-run state.orch deploy.lib.update_nodes_tg pillar='{"region": "us-west-2", "tg_name": "ichttp-dev3-target-external", "batch": "50%"}' saltenv=dev3 -l info

batch defaults to 25%

#}


{% from 'orch/map.jinja' import saltenv with context %}
{% set region = salt['pillar.get']('region', None) %}
{% set tg_name = salt['pillar.get']('tg_name', None) %}
{% set batch = salt['pillar.get']('batch', '25%') %}
{% set instance_ids = [] %}
{% set instance_lookup = {'names': {}} %}
{% set tg_health_info = salt.saltutil.runner('eb_boto3_elbv2.describe_target_health', kwarg={'name': tg_name, 'region': region}) %}


{# Parameter validation #}

{% set errors = [] %}

{% for param in ['region', 'tg_name', 'batch'] %}
{% if param not in pillar %}
{% do errors.append(param ~ " is a required parameter") %}
{% endif %}
{% endfor %}

{% if errors|length > 0 %}
preflight_check:
  test.configurable_test_state:
    - name: Additional information required...
    - changes: False
    - result: False
    - comment: "{{ errors|join(', ') }}"
{% else %}
preflight_check:
  test.succeed_without_changes:
    - name: "All parameters accepted"
{% endif %}

{% for tg_id in tg_health_info %}
  {% set instance_id =  tg_id['Target']['Id'] %}
  {% set instance_port = tg_id['Target']['Port'] %}
  {# build list of instance ids so we can figure out batching afterwards #}
  {% do instance_ids.append(instance_id) %}
  {% set instance_name = salt['boto_ec2.get_tags'](instance_id=tg_id['Target']['Id'], region=region) %}
  {# adding the instance id -> name and port info to a lookup table so we can reference it later #}
  {% do instance_lookup.update({'port' : instance_port}) %}
  {% do instance_lookup['names'].update({instance_id: instance_name[3]['Name']}) %}
{# sample instance_lookup dict:
{
  'port': 8080,
  'names': {
    'i-123089123908': 'minion1',
    'i-098390248234': 'minion2'
  }
}
#}
{% endfor %}

{% if instance_ids|length == 0 %}
deploy.lib.update_nodes_tg.input-error:
  test.configurable_test_state:
    - name: No instances in targetgroup to highstate.
    - changes: False
    - result: False
    - comment: |
        There were no instance ids found in the targetgroup. Please check the name of the targetgroup to confirm it is suppose to be empty.
        Examples:
        salt-run state.orch deploy.lib.update_nodes_tg pillar='{"region": "us-west-2", "tg_name": "ichttp-dev3-target-external", "batch": "50%"}' saltenv=dev3 -l info
{% else %}

  {# batching logic starts here #}
  {# This will accomodate if someone uses % sign or not #}
  {% set batch_in_pillar = salt['pillar.get']('batch', '25%') %}
  {% if batch_in_pillar[-1:] == '%' %}
    {% set batch_percent = pillar['batch'][:-1]|int / 100 %}
    {% set batch_count = ( batch_percent * instance_ids|length )|round|int %}
  {% else %}
    {% set batch_count = pillar['batch']|int %}
  {% endif %}

  {# if batch_count is 0, use a value of 1 #}
  {% if batch_count == 0 %}
    {% set batch_count = 1 %}
  {% endif %}
  {% if ( batch_count == instance_ids|length ) and ( batch_in_pillar != '100%' ) and ( instance_ids|length != 1 ) %}
    {% set batch_count = batch_count - 1 %}
  {% endif %}
  
  {% set instance_ids_batched = [] %}
  {% set tempdict = {} %}
  {% for item in instance_ids %}
    {% set instance_ids_index = loop.index - 1 %}
    {% set mylist_index = loop.index - 1 %}
    {% set last_index = mylist_index|int %}
  
    {# if this is the first instance, just add it #}
    {% if loop.index == 1 %}
      {% do tempdict.update({loop.index|string: [item]}) %}
    {% elif ( instance_ids[instance_ids_index:]|length >= batch_count ) and ( last_index == batch_count ) %}
      {% do tempdict.update({loop.index|string: [item]}) %}
    {% elif ( instance_ids[instance_ids_index:]|length < batch_count ) and ( last_index == batch_count ) %}
      {% do instance_ids_batched.append(instance_ids[instance_ids_index:]) %}
      {% break %}
    {% else %}
      {% set newlist = tempdict[last_index|string] %}
      {% do newlist.append(item) %}
      {% do tempdict.update({loop.index|string: newlist}) %}
      {% if newlist|length == batch_count %}
        {% do instance_ids_batched.append(newlist) %}
      {% endif %}
    {% endif %}
  {% endfor %}
  {# batching logic ends here #}

{#
  # instance_ids_batched: [['i-09e354fae790dcffd', 'i-0f05fe50445eb2f23'], ['i-0a0ba92dcd0a7dfbb', 'i-070dac0a34c15c4af']]
    # instance_group: ['i-1', 'i-2']
#}
  {% for instance_group in instance_ids_batched %}
    {% set instances = [] %}
    {% set minion_ids = [] %}
    {% for instance_id in instance_group %}
      {% do instances.append({'id': instance_id, 'port': instance_lookup['port']}) %}
      {% do minion_ids.append(instance_lookup['names'][instance_id]) %}
    {% endfor %}

{#

  # instances: [{'id': 'i-1', 'port': 9100}, {'id': 'i-2', 'port': 9100}]
  # minion_ids: ['minion1', 'minion2']
#}

{# ****** ADD SALT PROCESS TO DEREGISTER/VERIFY/HIGHSTATES/REREGISTER/VERIFY #}
{{ sls }}.deregister.instance.{{minion_ids|join('_')}}.from.target.group.{{tg_name}}:
  salt.runner:
    - name: eb_boto3_elbv2.deregister_instances
    - targetgroupname: {{ tg_name }}
    - targets: {{ instances }}
    - region: {{ region }} 

{{ sls }}.verify.target.deregistered.for.{{minion_ids|join('_')}}:
  salt.runner:
    - name: eb_boto3_elbv2.verify_target_status
    - targetgroupname: {{ tg_name }}
    - targets: {{ instances }}
    - region: {{ region }}
    - status: absent
    - timeout: 60
    - watch:
       - salt: {{ sls }}.deregister.instance.{{minion_ids|join('_')}}.from.target.group.{{tg_name}}

{{ sls }}.highstate.{{minion_ids|join('_')}}:
  salt.state:
    - tgt: {{ minion_ids|join(',') }} # "minion1,minion2"
    - tgt_type: list
    - highstate: true
    - timeout: 3600
    - saltenv: {{ saltenv }}
    - watch:
      - salt: {{ sls }}.verify.target.deregistered.for.{{minion_ids|join('_')}}

{{ sls }}.register.instance.{{minion_ids|join('_')}}.to.target.group.{{tg_name}}:
  salt.runner:
    - name: eb_boto3_elbv2.register_instances
    - targetgroupname: {{  tg_name }}
    - targets: {{ instances }}
    - region: {{ region }}
    - watch:
      - salt: {{ sls }}.highstate.{{minion_ids|join('_')}}

{{ sls }}.verify.target.registered.for.{{minion_ids|join('_')}}:
  salt.runner:
    - name: eb_boto3_elbv2.verify_target_status
    - targetgroupname: {{ tg_name }}
    - targets: {{ instances }}
    - region: {{ region }}
    - status: healthy
    - timeout: 60
    - failhard: True # do not loop again if this fails
    - watch:
       - salt: {{ sls }}.register.instance.{{minion_ids|join('_')}}.to.target.group.{{tg_name}}
  {% endfor %}
{% endif %}
