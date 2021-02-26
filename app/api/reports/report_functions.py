from dateutil import parser
import pytz
import csv
from app.schemas import TaskSchema

csv_columns = ["time_of_call", 'time_dropped_off',
               'priority', 'time_cancelled', 'patch', 'assigned_riders_display_string', 'time_picked_up',
               'pickup_address', 'deliverables', 'comments', 'requester_contact',
               'dropoff_address', 'time_created', 'time_rejected']


def convert_time(isostring):
    d = parser.parse(isostring)
    return d.astimezone(pytz.timezone('Europe/London')).strftime('%d-%m-%Y %H:%M')


def generate_csv_from_tasks(tasks, write_path):
    schema = TaskSchema(many=True, exclude=('links',))
    tasks = schema.dump(tasks)
    try:
        with open(write_path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, extrasaction="ignore")
            writer.writeheader()
            for t in tasks:
                t["time_of_call"] = convert_time(t["time_of_call"])
                if t["time_rejected"]:
                    t["time_rejected"] = convert_time(t["time_rejected"])
                try:
                    t["comments"] = ", ".join([c["body"] for c in t["comments"]])
                except:
                    pass
                try:
                    t["requester_contact"] = "{}, {}".format(t["requester_contact"]["name"],
                                                             t["requester_contact"]["telephone_number"])
                except:
                    pass
                try:
                    t["priority"] = "Non-urgent" if t["priority"] == "Standard" else t["priority"]
                except:
                    pass

                try:
                    pickup_address = t["pickup_location"]["address"]
                    t["pickup_address"] = "{}, {}".format(pickup_address["ward"], pickup_address["line1"]) if \
                        pickup_address["ward"] else pickup_address["line1"]
                except Exception as e:
                    pass
                try:
                    dropoff_address = t["dropoff_location"]["address"]
                    t["dropoff_address"] = "{}, {}".format(dropoff_address["ward"], dropoff_address["line1"]) if \
                        dropoff_address["ward"] else dropoff_address["line1"]
                except Exception as e:
                    pass
                try:
                    t["time_dropped_off"] = convert_time(t["time_dropped_off"])
                except Exception as e:
                    pass
                try:
                    t["time_picked_up"] = convert_time(t["time_picked_up"])
                except Exception as e:
                    pass
                try:
                    print(t["deliverables"])
                    t["deliverables"] = ", ".join([d["type"] for d in t["deliverables"]])
                except Exception as e:
                    print(e)
                writer.writerow(t)
    except IOError:
        print("I/O Error")
