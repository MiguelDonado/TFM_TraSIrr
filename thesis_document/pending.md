- [] Check the captions make the figures self contained
- [] Explicitly mention that there are several concepts of convergence, from the marl point of view when agents stop updating its policies, and from the traffic sense when it reaches DUE.
- [] I could also say that a contribution was a new heuristic to search for a set of paths for an OD pair, usually they did k-shortest path.
- [] Mention I used MLflow
- [] Mention which sumo version im using.
- [] Add explanation of why R-gap can be negative
- [] Decirles de quedar la semana que viene. Darles varios dias para leer la thesis
- [] Add Molano last paper LLM to literature review
- [] Add the traffic assignment map that i did in DRAWIO. It is in downloads
- [] Put evaluation paragraph comparing RL approach vs Classic approach in literature review
- [] Explain properly the difference between classic traffic assignment and MARL approach. One uses flow update algorithms such as MSA that try to solve and update flows to get to an equilibrium, whereas MARL just update policies of agents based on past experiences and stopped when some number of iterations or when policies converge, but it does not try to solve any equilibrium, instead equilibrium may emerge naturally. It individually update route choice, whereas in classic assignment it updates aggregate flows to get to equilibrium instead of individually.

- [] Explain all the extensions gotchas that I wrote in code comments, but on the latex. I think some of those detail explanations of why I used some formulas may be useful.
- [] Mention that the nonlinear extension captures the intuition of the 4th assumption of BM framework, and the waiting time averse and risk averse captures the intuition of the 3th assumption of BM framework.
- [] Mention that thesis is modelling the morning and evening peak periods related to work-related commutes.
- [] I can even talk from my own experience, with rodalies in BCN and buses. I prefer to take a bus even if its a bit longer but more reliable.
- [] Explain route choice can be day-to-day or within 
- [] Acabar de leer todas las cosas que ponga en las referencias  
- [] Añadir lineas best case scenario y worst case scenario 
- [] En las graficas usar pocos colores 
- [] En las graficas de los flow solo marcar los disrupted con la label (los otros se entienden por contraposicion que no estan disrupted). Las mas relevantes mas gordas las que no importa en gris
- [] Llamarlo warm-up instead of pre-learning
- [] Solucionar que al hacer lo de las referencias solo aparezca el numero
- [] Lo del 90 percentil no quedo claro. Coger el worst case

- [] Add to dedicatory "And to David Goggins, Kobe Bryant, and the other role models who helped me change my inner dialogue. As Goggins said, “Never pick the easy road.”
- [] Revisar formulas paper 

- [] Traffic dynamics can be modeled in continuous time, implying that travelers update their decision in real time. However, such an assumption is generally unrealistic, since individuals do not continuously replan their routes while traveling. Instead, it is more appropriate to adopt a discrete time framework, in which travelers make decisions at specific intervals. The way time is discretized depends on the moments at which drivers are assumed to make routing decisions. In some approaches, travelers revise their route choices between consecutive days based on previous travel experiences, leading to so-called day-to-day models. In other approaches, decisions are updated dynamically at road intersections during the trip, resulting in junction-level models. Since the objective is to model the behavior and decision-making processes of drivers, the problem can be naturally formulated as a sequential decision-making problem, for which reinforcement learning provides a suitable framework.

- [] Include a summary figure that places what im doing in all the traffic assignment and bounded rationality structure that i explained in background and in traffic modelling and simulation
- [] Be explicit and mention that Im using a classical RL algorithm, not a modern RL like Q-learning...
- [] This BRUE formulation has been helpful in explaining observed changes in network flows after a disruption. For instance, assume that a link is removed from the network due to a disaster of some sort, and that flows adjust towards a new equilibrium in the network without the affected link. When the link is restored, flows will adjust again. If the principle of user equilibrium is true, the flows will move back to exactly the same values as before. However, in practice there has been some “stickiness” observed, and not all drivers will return to the same routes they were initially on. The BRUE framework provides a logical explanation for this: when the network is disrupted, certain drivers were forced to choose new paths. When the network is restored, they will only switch back to their original paths if the travel time savings are sufficiently large. Otherwise, they will remain on their new paths.
- [] Lo de que el DTA se computa teniendo en cuenta los experienced travel time instead of the instantaneous travel time (Book: Transportation Network Analysis) ponerlo en la thesis, puesto que me resulto muy intuitivo y aclaratorio. Pag 28/701
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

