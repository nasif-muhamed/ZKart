
from pychartjs import BaseChart, ChartType, Color as colorful

class BarChartOrderStatus(BaseChart):
    def __init__(self, labels, success_data, progress_data, return_data):
        self.labels.labels = labels
        self.data.Success.data = success_data
        self.data.Progress.data = progress_data
        self.data.Return.data = return_data

    type = ChartType.Bar

    class labels:
        labels = []

    class data:
        class Success:
            label = 'Delivered'
            backgroundColor = colorful.Green
            data = []

        class Progress:
            label = 'In Progress'
            backgroundColor = colorful.Yellow
            data = [] 

        class Return:
            label = 'Returned & Cancelled'
            backgroundColor = colorful.Red
            data = [] 

class BarChartSingle(BaseChart):
    def __init__(self, backgroundColor, label, labels, data):
        self.data.label = label
        self.labels.labels = labels
        self.data.data = data
        self.data.backgroundColor = backgroundColor

    type = ChartType.Bar

    class labels:
        labels = [] 

    class data:
        label = ''
        backgroundColor = "rgba(75, 192, 192, 0.2)"
        data = [] 
