from datetime import datetime, timedelta


class Node:
    def __init__(self, id, x, y, d=0,
                 t0: datetime = 0, t1: datetime = 1,
                 p0: timedelta = 0, p1: timedelta = 0,
                 start_day: datetime = None,
                 service: timedelta = 0):
        self.id = id
        self.x = x
        self.y = y
        self.demand = d
        self.time_window = [t0, t1]
        self.time_window_s = [(t0 - start_day).total_seconds(), (t1 - start_day).total_seconds()]
        self.penalty = [p0, p1]
        self.penalty_s = [p0.total_seconds() if isinstance(p0, timedelta) else p0,
                          p1.total_seconds() if isinstance(p1, timedelta) else p1]
        self.service = service
        self.service_s = service.total_seconds() if isinstance(service, timedelta) else service

    def __repr__(self):
        # Formatowanie okna czasowego na HH:MM
        t0_human = self.time_window[0].strftime("%H:%M")
        t1_human = self.time_window[1].strftime("%H:%M")

        # Opcjonalnie: formatowanie czasu obsługi (service) jeśli jest timedelta
        # Zakładając, że service to timedelta, wyciągamy minuty
        service_min = int(self.service_s // 60) if hasattr(self, 'service_s') else self.service

        return (f"Node(id={self.id}, x={self.x}, y={self.y}, "
                f"demand={self.demand}, time=[{t0_human}-{t1_human}], "
                f"service={service_min}min)")