- [] Ver si el modelo mas irracional llega a DUE. Sino llegara entonces seria muy relevante, porque daria a indicar
  que DUE no es para nada realista.
- [] Memoria corta. Recomendacion 60 paginas y anexos.
- [] Añadir que he utilizado la IA  
- [] Make the thesis to be focused on my contribution
- [] Define somewhere in the thesis the edge nomenclature
- [] Mencionar en los caption que parámetros he usado (memory level, learning rate)
- [] Cite or incorpore my own Thompson Sampling project.
- [] Let clear, what it means a simulation, an episode, a time interval, experiment run (some explanatory figure may ease understanding)
- [] Briefly acknowledge on the thesis that Im applying TDSP on a non-FIFO table. Example paragraph:
    - The time-dependent shortest-path calculations were performed on discretized average link travel-time tables extracted from SUMO. Due to temporal aggregation, some link travel-time profiles do not strictly satisfy the FIFO property. Consequently, the TDSP computations should be interpreted as approximate shortest paths. However, the resulting Rgap values exhibited the expected convergence behavior, both during Bush-Mosteller learning and during DUA iterations, suggesting that the impact of these violations is limited for the studied scenarios.
- [] A principle of experimental design is to fix parameters in an order that respects their dependencies. Every parameter should be evaluated under the conditions in which it will actually be used. If one parameter depends on another, the latter should be fixed first.
- [] Explian what I saw in the paper where does this road go, that we trust more the information that we got from experience, than from Google Maps, internal information. This is a motivation to defend that even though exists Google Maps, that does not mean all people act ratioanlly. For example, sometimes google maps show us the shortest route, but warn us that there is some maintainance or congestion and that we should take another better alternative. Even so, we believe it wont be that bad and go on the "shortest route" that may not be the shortest anymore because of congestion...
- [] Pagina con la notacion y abreviaturas
- [] Incorporate the conclusions and results in the abstract
- [] Literature review (state of the art). Related papers. At the end say which limitations
- [] Things they told me in the meeting to change:
  1. After literature review, SUMO outline
  2. Research questions: Ponerlas al principio en los objetivos, y luego en las conclusiones lo menciono.
  3. En results: Poner preguntas y responder
- [] Para todo lo que vaya antes del cuerpo de la monografía (contenido de mi thesis) utilizar una numeración, para el contenido de mi thesis utilizar otra numeración que empieze desde 1 de nuevo.
- [] Dont worry about list of figures and tables being added to the toc. Is the way this class works.
- []

-  ### Non-study hyperparameters
1. Perform sensitivity analysis on hyperparameters that directly influence the learning algorithm
   or the r-gap values:
   - min_distance_factor
   - random_factor
   - n_routes_per_od
   - threshold_density
   - warm_up_time
   - fixed_time_min
   - fixed_time_interval (yes)
2. Fix implementation/computational hyperparameters using reasonable choices (without the need to 
   perform sensitivity analysis), unless evidence that they materially affect the results:
   - network
   - tolerance_demand_calibration
   - max_size_od_space
   - simulation_time
   - routing_algorithm
   - max_attempts
   - n_threads
   - max_episodes
   - tolerance_stopping_rule
   - k_no_change
   - heuristic_veh_km_hour_initial_guess
   - fringe_factor
   - duaIterate_max_iterations
   - duaIterate_step_length


- [] Meet format requisites
- [ ] **Evitar plagio**: La thesis debe haber sido revisada por el software Ouriginal (https://bibliotecnica.upc.edu/es/propietat-intellectual/ouriginal)
- [ ] **Citas y bibliografia** (referencias)
- [ ] **Numeración**

- Los **epígrafes de capítulos, apartados y subapartados** deben aparecer jerarquizados por la tipografía y con números arábigos subdivididos por puntos. Por ejemplo:


  - 2. capítulo

    - 2.1 Apartado
      - 2.1.1 Subapartado

- Los **anexos** se identificarán por letras mayúsculas consecutivas. Por ejemplo:


  - anexo A
  - anexo B
  - anexo C

- Los trabajos se presentan en **hojas escritas a dos caras**.

- **Todas las hojas**, Salvo la portada, las hojas de respeto y el sumario, **deben estar numerados con un número arábigo** normalmente colocado en el pie de la hoja que comenzará por el número 3 o 4 en función del número de hojas sin numerar que haya al principio.

