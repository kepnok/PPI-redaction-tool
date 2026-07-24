from faker import Faker
from typing import Dict, Any

class FakeDataAnonymizer:
    """Class to generate fake data for specific entity types using Faker."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        seed = self.config.get("faker_seed", 42)
        Faker.seed(seed)
        self.fake = Faker(['en_IN', 'en_US'])
        self.mapping = {}
        
    def get_fake_value(self, entity_type: str, original_value: str) -> str:
        """Returns a fake value corresponding to the given entity type, consistently mapped."""
        if original_value in self.mapping:
            return self.mapping[original_value]
            
        def _generate():
            if entity_type == "PERSON":
                return self.fake.name()
            elif entity_type == "EMAIL_ADDRESS":
                return self.fake.email()
            elif entity_type == "PHONE_NUMBER":
                return self.fake.phone_number()
            elif entity_type == "LOCATION":
                return self.fake.city()
            elif entity_type == "ORGANIZATION":
                return self.fake.company()
            elif entity_type == "US_SSN":
                return self.fake.ssn()
            elif entity_type == "CREDIT_CARD":
                return self.fake.credit_card_number()
            elif entity_type == "DATE_TIME":
                return self.fake.date()
            elif entity_type == "IP_ADDRESS":
                return self.fake.ipv4()
            elif entity_type == "IN_PAN":
                # Generate a fake PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
                letters = self.fake.lexify(text='?????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                digits = self.fake.numerify(text='####')
                letter = self.fake.lexify(text='?', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                return f"{letters}{digits}{letter}"
            elif entity_type == "IN_AADHAR":
                # Generate a fake Aadhar: 12 digits
                return self.fake.numerify(text='#### #### ####')
            elif entity_type == "IN_SEBI":
                # Generate a fake SEBI: IN + 10 alphanumeric
                suffix = self.fake.lexify(text='??????????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                return f"IN{suffix}"
            elif entity_type == "IN_CIN":
                # Generate a fake CIN: U + 5 digits + MH + 4 digits + PLC + 6 digits
                l_or_u = self.fake.random_element(elements=('L', 'U'))
                d5 = self.fake.numerify(text='#####')
                state = self.fake.lexify(text='??', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                year = self.fake.numerify(text='20##')
                type_code = self.fake.lexify(text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                d6 = self.fake.numerify(text='######')
                return f"{l_or_u}{d5}{state}{year}{type_code}{d6}"
            else:
                return f"<{entity_type}>"
                
        val = _generate()
        self.mapping[original_value] = val
        return val
