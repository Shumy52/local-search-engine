class WidgetManager:
    """
    Manages the detection and rendering of widgets based on search queries.
    """
    
    def __init__(self):
        # Define widget triggers - terms that activate specific widgets
        self.widget_triggers = {
            'calculator': {
                'name': 'calculator',
                'title': 'Calculator',
                'template': 'widgets/calculator.html'
            },
            'weather': {
                'name': 'weather',
                'title': 'Weather',
                'template': 'widgets/weather.html'
            },
            'timer': {
                'name': 'timer',
                'title': 'Timer',
                'template': 'widgets/timer.html'
            }
        }
    
    def get_widgets_for_query(self, query) -> list:
        """
        Determine which widgets to display based on the search query.
        
        Args:
            query: The search query string
            
        Returns:
            List of widget configurations to display
        """
        if not query:
            return []
            
        query_lower = query.lower()
        widgets = []
        
        # A bit unorthodox, to return a list of widgets
        # But HTML handles it well, and what should one do if the user searches 
        # for all of them at once?
        for trigger, widget_config in self.widget_triggers.items():
            if trigger in query_lower:
                widgets.append(widget_config)
                
        return widgets