class CustomFilter(object):
    def __init__(self, name, login_name, parameter,
                 search_term, inversed):
        self.name = name
        self.login_name = login_name
        self.parameter = parameter
        self.search_term = search_term
        self.inversed = inversed

    def to_dictionary(self):
        result = {
            'name': self.name,
            'loginName': self.login_name,
            'parameter': self.parameter,
            'searchTerm': self.search_term,
            'inversed': self.inversed
        }

        return result
