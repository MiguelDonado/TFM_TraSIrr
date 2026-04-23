This files describe the pipeline to build a network from a real city (Santiago de Compostela, Barcelona...)

1. Visit overpass turbo (web used to run Overpass queries)
https://overpass-turbo.eu/

2. Once you are on that page
   1. Zoom to the area you wanna export
   2. Ask ChatGPT for the Overpass query you want:
      -  Example: 
         -  Download:
            - vehicle-only road network
            - avoid weird small roads (like parking/service)
  
            ```sh
                [out:xml][timeout:25][bbox:{{bbox}}];

                (
                way["highway"~"motorway|trunk|primary|secondary|tertiary|residential"]
                    ["service"!~".*"]
                    ["access"!~"private"];
                );

                (._;>;);
                out body;
            ```
       - The bbox: Is the visible rectangle (is what we used in our query)
    3. Use netconvert:
       - So we can convert the .osm to a SUMO network
       - And we can remove traffic lights with the conversion
       - Use the /home/miguel/6.Projects/Thesis/src/scripts/netconvert.py script
