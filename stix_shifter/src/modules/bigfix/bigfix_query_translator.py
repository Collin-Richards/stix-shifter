
from ..base.base_query_translator import BaseQueryTranslator


class BigfixQueryTranslator(BaseQueryTranslator):

    def transform_query(self, data, options, mapping=None):
        """
        Takes in passed in query string and returns it
        :param data: query string that gets returned
        :type data: str
        :param mapping: This is unused
        :type mapping: str
        :return: the passed in data
        :rtype: str
        """
        # transform query...
        return data
