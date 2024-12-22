# HealthyStool

_Family Stool Tracker_

A Flask-based web application designed to help parents monitor their family members' bowel movements using the Bristol Stool Scale. This tool is particularly useful for parents with children who have digestive issues or for those who need to report bowel movement patterns to healthcare providers.

## About the Bristol Stool Scale

The Bristol Stool Scale is a medical aid designed to classify feces into seven groups. It was developed by Heaton and Lewis at the University of Bristol and was first published in the Scandinavian Journal of Gastroenterology in 1997.

### The Seven Types:

1. **Type 1:** Separate hard lumps (severe constipation)
2. **Type 2:** Lumpy and sausage-like (mild constipation)
3. **Type 3:** Sausage-shaped with cracks (normal)
4. **Type 4:** Smooth, soft sausage (normal)
5. **Type 5:** Soft blobs with clear edges (lacking fiber)
6. **Type 6:** Mushy with ragged edges (mild diarrhea)
7. **Type 7:** Liquid without solid pieces (severe diarrhea)

## Benefits of Tracking

- **Medical Documentation**: Provides accurate records for healthcare providers
- **Pattern Recognition**: Helps identify dietary triggers and health issues
- **Health Monitoring**: Assists in monitoring digestive health over time
- **Treatment Effectiveness**: Helps evaluate if treatments or dietary changes are working

## Technical Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML, CSS (Bootstrap DCN)
- **Time Management**: PyTZ for timezone handling

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/poop-tracker.git
cd poop-tracker
```

1. Create and activate a virtual environment:

I am currently using `3.10`

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

1. Install required packages:

```bash
pip install -r requirements.txt
```

1. Set up the database:

```bash
flask db upgrade
```

1. Run the application:

```bash
python poop_app.py
```

The application will be available at `http://localhost:5000`

## Features

- User registration and authentication
- Add multiple family members
- Record bowel movements with timestamp
- Track stool type using Bristol Stool Scale
- View history of records
- Timezone support

## Configuration

The application uses SQLite by default. To modify the timezone, update the following line in `poop_app.py`:

```python
local_tz = pytz.timezone('America/Caracas')  # Change to your timezone
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Todo

- [ ] Ability to edit and delete records
- [ ] Ability to edit family members
- [ ] UTC time support
- [X] New UI design and theme
- [ ] Calendar view of records
- [ ] More detailed information on each stool type
- [ ] Additional data visualizations (charts)
- [ ] Ability to export records as CSV, PDF
- [ ] Forgot password functionality

## License

[MIT](https://choosealicense.com/licenses/mit/)
