from random import randint


class VerificationCode:
    def generate(self):
        """
        Generate a random 6 digit string of numbers.
        We use this formatting to allow leading 0s.
        """
        self.code = self.__generate_numeric_token()
        return self.code

    def mail(self):
        """
        Mail the generated random 6 digit string of numbers to user's email address
        """
        return False

    def generate_and_mail(self):
        """
        Mail the generated random 6 digit string of numbers to user's email address
        """
        self.generate()
        self.mail()

        return self.code

    def __generate_numeric_token(self):
        """
        Generate a random 6 digit string of numbers.
        We use this formatting to allow leading 0s.
        """
        return str("%06d" % randint(0, 999999))
