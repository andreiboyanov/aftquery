
def _get_name_and_id(name_and_id):
    first_bracket_index = name_and_id.find('(')
    _name = name_and_id[:first_bracket_index-1]
    _id = name_and_id[first_bracket_index+1:-1]
    return _name, _id


