class DBRouter(object):
    def db_for_read(self, model, **hints):
        """
        All reads are routed to Reader
        """
        return 'Reader'

    def db_for_write(self, model, **hints):
        """
        All writes are routed to Writer
        """
        return 'Writer'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Returning
        None
        means
        that
        no
        specific
        routing
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Returning None means that no specific routing
        """
        return True
