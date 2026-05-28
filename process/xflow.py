from datetime import datetime


def afsend_til_xflow(xflow_process_client, procesid: str, addresse: str, rettighedsgruppe: int,):
    blanket_data = {
        "formValues": [
            {
                "elementIdentifier": "RPASignatur",
                "valueIdentifier": "Tekst",
                "value": "Behandlet af Tyra (RPA)",
            },
            {
                "elementIdentifier": "RPABehandletDato",
                "valueIdentifier": "Dato",
                "value": datetime.today().strftime("%d-%m-%Y"),
            },
            {
                "elementIdentifier": "Textfield-RPA-Skole",
                "valueIdentifier": "Tekst",
                "value": addresse,
            },
        ]
    }
    xflow_process_client.update_process(procesid, blanket_data)
    xflow_process_client.advance_process(procesid, rettighedsgruppe)
