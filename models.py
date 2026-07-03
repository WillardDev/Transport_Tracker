from datetime import datetime


class SACCO:
    def __init__(self, name, code):
        self.name = name
        self.code = code
        self.routes = []

    def add_route(self, route):
        self.routes.append(route)

    def route_count(self):
        return len(self.routes)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Route:
    def __init__(self, route_number, start, end, sacco=None):
        self.route_number = route_number
        self.start = start
        self.end = end
        self.sacco = sacco
        self.fares = []

    def add_fare(self, fare):
        self.fares.append(fare)

    def latest_fare(self):
        return self.fares[-1] if self.fares else None

    def fare_history(self):
        return sorted(self.fares, key=lambda f: f.date, reverse=True)

    def __str__(self):
        sacco_name = self.sacco.name if self.sacco else "Unknown"
        return f"Route {self.route_number}: {self.start} -> {self.end} [{sacco_name}]"


class Fare:
    def __init__(self, amount, date=None, weather=None):
        self.amount = amount
        self.date = date if date else datetime.now().strftime("%Y-%m-%d")
        self.weather = weather

    def __str__(self):
        weather_str = f" ({self.weather})" if self.weather else ""
        return f"KSh {self.amount} on {self.date}{weather_str}"
