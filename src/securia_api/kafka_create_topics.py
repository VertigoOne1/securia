#!/bin/python3

from confluent_kafka.admin import AdminClient, NewTopic

# Define the Kafka broker connection details
broker_config = {
    'bootstrap.servers': 'pkc-75m1o.europe-west3.gcp.confluent.cloud:9092',
    'sasl.mechanism': 'PLAIN',
    'security.protocol': 'SASL_SSL',
    'sasl.username': 'CKAIQQL2ORAJ3KHI',
    'sasl.password': 'xWhgyXU3MCgRttZANOkUHLCNzz9Ug3EtZinIBo0o+LEXh7cYoAoWbE6NdhUA17ny'
}

# Create the AdminClient instance
admin_client = AdminClient(broker_config)

# Define the new topics
new_topics = [
    NewTopic("telemetry-v1", 3, 3),
    NewTopic("alarms-v1", 3, 3)
]

# Create the topics
try:
    fs = admin_client.create_topics(new_topics)
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print(f"Topic {topic} created")
        except Exception as e:
            print(f"Failed to create topic {topic}: {e}")
except Exception as e:
    print(f"Failed to create topics: {e}")

# List all available topics
try:
    metadata = admin_client.list_topics()
    topics = metadata.topics
    print("Available topics:")
    for topic_name in topics.keys():
        print(f"- {topic_name}")
except Exception as e:
    print(f"Failed to list topics: {e}")


# Define the topic to be deleted
topic_name = 'telemetry_v1'

# Delete the topic
try:
    futures = admin_client.delete_topics([topic_name])
    for topic, future in futures.items():
        try:
            future.result()
            print(f"Topic {topic} deleted successfully")
        except Exception as e:
            print(f"Failed to delete topic {topic}: {e}")
except Exception as e:
    print(f"Failed to delete topics: {e}")