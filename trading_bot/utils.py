from json import JSONEncoder
import datetime

class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            return JSONEncoder.default(o=obj)
    
