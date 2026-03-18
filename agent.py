import numpy as np
import tensorflow as tf
import tensorflow.compat.v1 as tf

tf.disable_v2_behavior()


class SumTree(object):
    """
    Data structure to implement Prioritized Experience Replay (PER)

    Simple steps of PER
        1. Store experiences in a replay buffer.
        2. Compute priority for each experience (often |TD error|).
            > Here we want to sample experiences which are new in the memory buffer
            > So we use the rank of the experience to compute its priority
            > rank(i): position of transition i when experiences are sorted by recency
        3. Sample experiences with probability proportional to priority.
        4. Update priorities after learning.

    The tree represents a cumulative distribution function (CDF).

    Sampling works like inverse transform sampling.

    """

    data_pointer = 0

    def __init__(self, capacity):
        """
        capacity: Maximum number of experiences the replay memory can store

        Capacity determines:
        1. Size of stored experiences: self.data
        2. Size of priority tree: self.tree
        """
        self.capacity = capacity

        """
        Create the tree (it stores priorities not experiences)
        The reason for the tree structure instead of a simple list is
        efficiency when sampling according to priorities

    Tree structure
        [0]
       /   \
     [1]   [2]
    /  \   /  \
  [3] [4] [5] [6]

        Leaves (last layer) store the priorities
        Internal nodes store sum of children priorities

        Example priorities: p = [1, 2, 3, 4]

    Tree becomes
        10
       /  \
      3    7
     / \  / \
    1  2 3  4

        The root is the total priority

        See more details in Theory/PER
        """
        self.tree = np.zeros(2 * capacity - 1)

        # Replay buffer
        # Each experience stored is (st,at,rt,st+1)
        # Example: self.data[0] = (s1,a1,r1,s2)
        #          self.data[1] = (s2,a2,r2,s3)
        self.data = np.zeros(capacity, dtype=object)

    def add(self, p, data):
        """
        Insert a new experience with priority p
        """
        # Find leaf index in the tree array where the new priority will be stored
        tree_idx = self.data_pointer + self.capacity - 1
        # Store experience
        self.data[self.data_pointer] = data
        # Update tree
        self.update(tree_idx, p)

        # Move data pointer
        self.data_pointer += 1

        # When capacity is reached:
        # It creates a circular buffer (old experiences overwritten)
        if self.data_pointer >= self.capacity:
            self.data_pointer = 0

    def update(self, tree_idx, p):
        """
        tree_idx: index in the tree array where the new priority will be stored
        p: new priority value
        """

        """
        Compute the change (new_priority - old_priority (it there was some priority before))
        old priority = 0.3
        new priority = 0.8
        change = 0.5

        We need this change because all parent nodes store sums
        """
        change = p - self.tree[tree_idx]

        # Update the leaf
        self.tree[tree_idx] = p

        """
        Propagate the change up the tree
        
    Example tree
        10
       /  \
      3    7
     / \  / \
    1  2 3  4

    Suppose we update leaf 3 -> 5
    change = +2
    
    Then:
    parent += 2
    root += 2
    
    New tree
        12
       /  \
      3    9
     / \  / \
    1  2 5  4
        """

        while tree_idx != 0:
            tree_idx = (tree_idx - 1) // 2
            self.tree[tree_idx] += change

    def get_leaf(self, v):
        """
        Sampling experiences

        v ~ Uniform(0, total_priority)
        The root stores: total_priority
        """

        """
        Traversing the tree
        """

        # Start from root
        parent_idx = 0

        while True:

            # Left child
            cl_idx = 2 * parent_idx + 1
            # Right child
            cr_idx = cl_idx + 1

            """
            Detect when the traversal has reached a leaf node

Example:            
index:   0
        / \
       1   2
      / \ / \
     3  4 5  6

Imaging we are on leaf node = 3 (parent_idx)
cl_idx = 2*3 + 1 = 7
len(tree) = 7
7 >= 7  → True  

Therefore node 3 is a leaf
            """
            if cl_idx >= len(self.tree):
                leaf_idx = parent_idx
                break

            # Decision rule
            else:
                # Go left
                if v <= self.tree[cl_idx]:
                    parent_idx = cl_idx
                # Go right
                else:
                    v -= self.tree[cl_idx]
                    parent_idx = cr_idx

        # Retrieve index of experience in memory buffer
        data_idx = leaf_idx - self.capacity + 1
        return leaf_idx, self.tree[leaf_idx], self.data[data_idx]

    @property
    def total_p(self):
        """
        Root node stores the sum of the priorities

        This is used when sampling
        v = random.uniform(0, tree.total_p)
        """
        return self.tree[0]


class Memory(object):
    """
    Is implementing TD error logic, not recency as he states in the paper
    Complete implementation of PER on top of your SumTree

    It does 3 things:
    1. Store experiences with a priority
    2. Sample a minibatch according to priority
    3. Update priorities after learning

    Hyperparameters:
    epsilon: Avoid zero priority
    alpha: How strong priorization is (0 = uniform sampling, 1 = full priorization)
    beta: Correct bias (importance sampling)
    beta_increment: Gradually increases Beta to 1
    abs_err_upper: Clip large errors (stability)
    """

    epsilon = 0.01
    alpha = 0.2
    beta = 0.4
    beta_increment_per_sampling = 0.001
    abs_err_upper = 1.0

    def __init__(self, capacity):
        # Create the SumTree that stores experiences (data), priorities (tree)
        self.tree = SumTree(capacity)

    def store(self, transition):
        """
        Get max priority (extract all leaf priorities)
        Structure (example capacity = 4):
index:   0
        / \
       1   2
      / \ / \
     3  4 5  6
     Leaves = last capacity elements
     tree[-capacity:]
     tree[-4:] → indices [3,4,5,6]
        """
        max_p = np.max(self.tree.tree[-self.tree.capacity :])
        # If buffer is empty assign max priority (1)
        if max_p == 0:
            max_p = self.abs_err_upper
        # Insert experience with priority p on the tree
        self.tree.add(max_p, transition)

    def sample(self, n):
        """
        n: number of samples

        Sampling a minibatch
        Prepare the containers (b_idx, b_memory, ISWeights)

        We will return
        > Indices in tree
        > Sampled experiences
        > Importance sampling weights
        """
        b_idx = np.empty((n,), dtype=np.int32)
        b_memory = np.empty((n, self.tree.data[0].size))
        ISWeights = np.empty((n, 1))

        """
        Divide the whole priority range into n equal segments
        (stratified sampling)
        Example
        total = 10, n = 2
        segments:
        [0,5] and [5,10]
        """
        pri_seg = self.tree.total_p / n

        # Update beta (gradually increases to 1). In early training allow bias. Leter correct bias fully
        self.beta = np.min([1.0, self.beta + self.beta_increment_per_sampling])

        # Compute minimum probability (needed to normalize importance weights)
        min_prob = np.min(self.tree.tree[-self.tree.capacity :]) / self.tree.total_p

        # Sampling loop
        for i in range(n):
            """
            [a,b]=the i-th segment of the total priority range
            Example:

            total_p = 10
            n = 5
            pri_seg = 10 / 5 = 2

            Segments:
            i	a	b	interval
            0	0	2	[0,2]
            1	2	4	[2,4]
            2	4	6	[4,6]
            3	6	8	[6,8]
            4	8	10	[8,10]

            Each iteration picks a different slice of the CDF
            """
            a, b = pri_seg * i, pri_seg * (i + 1)
            # Sample one point per segment
            v = np.random.uniform(a, b)

            # Find leaf. This is the SumTree traversal (CDF inverse sampling)
            idx, p, data = self.tree.get_leaf(v)

            # Compute probability
            prob = p / self.tree.total_p

            # Importance sampling weight
            ISWeights[i, 0] = np.power(prob / min_prob, -self.beta)

            # Store results
            b_idx[i] = idx
            b_memory[i, :] = data

        # Return batch
        return b_idx, b_memory, ISWeights

    def batch_update(self, tree_idx, abs_errors):
        """
        Implementation of TD error logic

        After training, recompute TD errors logic
        """

        # Avoid zero
        abs_errors += self.epsilon
        # Clip large errors
        clipped_errors = np.minimum(abs_errors, self.abs_err_upper)
        # Compute priorities (alpha controls how strong prioritization is)
        ps = np.power(clipped_errors, self.alpha)

        # Update tree
        for ti, p in zip(tree_idx, ps):
            self.tree.update(ti, p)


class Agent:
    """
    The agent is DQN + Double DQN + Dueling Network + Prioritized Experience Replay
    """

    def __init__(
        self,
        n_features,
        n_actions,
        learning_rate=0.005,
        reward_decay=0.9,
        e_greedy=0.95,
        replace_target_iter=300,
        memory_size=10000,
        batch_size=32,
        e_greedy_increment=0.00001,
        output_graph=False,
        prioritized=True,
        double_q=True,
        dueling=True,
        sess=None,
        name="",
        saver="",
    ):
        """
        n_features: Size of the state vector (input to the neural network)
          The state vector it is [
            expected travel times in all roads,
            number of vehicles in all roads,
            pair of coordinates of destination,
            pair of coordinates of actual road
            ]

        n_actions: Number of possible actions (output size)
          Maximum number of outgoing edges in the network
          Moreover, the number of DNN outputs is dependent on the maximum number of connected
          roads in the network. However, in most cases roads in the network do not connect to
          the same number of roads in a network. Therefore, when the DRL agent decides to use
          the action that is based on DNN output, with the q values estimated by DNN,
          the DRL agent only selects the action with the highest q value among the
          number of connected roads and ignores the extras.
          For instance, assuming the maximum number of connected roads of a network is 4,
          and road AB only connects to road BC, BD and BE (3 actions).
          Based on the observation, DNN estimates 4 q-values [q1, q2, q3, q4] as output.
          In this case, DRL agent only selects the highest q-value among [q1, q2, q3] and
          ignores the q4 as it does not apply to any connected road.

        learning_rate: Step size for gradient descent
            high: fast learning but unstable
            low: slow but stable

        reward_decay: Discount factor
            0: Only inmediate reward
            ~1: Future matters as much as present

        e_greedy: Exploration (probability of choosing the best action)

        e_greedy_increment: At first we want to explore more, but we want it to decay as the agent learns

        replace_target_iter: Target network update (every 300 learning steps)

        memory_size: Number of stored transitions

        batch_size: Number of samples per training step

        prioritized: Use PER
            True: Sample important transitions
            False: Uniform sampling

        double_q: Use Double DQN (selection != evaluation)

        dueling: Use Dueling Network (value state + advantages)

        sess: Tensorflow session
            None: Create new session
            else: Reuse existing session

            This parameter session is needed, when:
                1. We have multiple agents / networks
                2. Training + evaluation together
                3. Save memory / GPU (share resources)
                4. Load pretrained model

        name: Used to build variable scopes (to avoid variable name collisions):

        Example usage:
        with tf.variable_scope(name + "eval_net"):
        name = "agent1_"
        agent1_eval_net/...
        agent1_target_net/...

        saver: Path to load pretrained model
        """

        """
        GPU configuration

        This tells TensorFlow:
        Dont allocate all GPU memeory at once - grow it as needed
        """
        # config = tf.ConfigProto()
        # config.gpu_options.allow_growth = True

        self.n_actions = n_actions
        self.n_features = n_features
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon_max = e_greedy
        self.replace_target_iter = replace_target_iter
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.epsilon_increment = e_greedy_increment

        """
        Epsilon setup
        If epsilon is increasing: 
            start at 0 (full exploration) and gradually increase it later
        Otherwise
            set epsilon to epsilon_max
        """
        self.epsilon = 0 if e_greedy_increment is not None else self.epsilon_max

        # Feature flags (which algorithmic components are active)
        self.prioritized = prioritized
        self.double_q = double_q
        self.dueling = dueling

        # Track how many training steps have happened
        self.learn_step_counter = 0

        """
        Creates.
        eval_net (training network)
        target_net (stable network)

        Defines loss, optimizer, placeholders
        """
        self._build_net(name)

        # Get network weights (target and eval networks)
        t_params = tf.get_collection("target_net_params")
        e_params = tf.get_collection("eval_net_params")

        """
        Define weight copy operation
        
        Example:
        target_w1 ← eval_w1
        target_w2 ← eval_w2 ...

        Does not execute them yet 
        Later:
        self.sess.run(self.replace_target_op)
        
        ¿What it is exactly?
        self.replace_target_op is a list of TensorFlow operations 
        tf.assign(t,e) does not execute anything.
        
        It creates an operation in the computation graph       
        “when executed → assign value of e to t”
        """
        self.replace_target_op = [tf.assign(t, e) for t, e in zip(t_params, e_params)]

        # Initialize memory (use SumTree-based PER)
        if self.prioritized:
            self.memory = Memory(capacity=memory_size)
        # Simple array [s, a, r, s']
        else:
            self.memory = np.zeros((self.memory_size, n_features * 2 + 2))

        # Saves model weights
        # self.saver is an object with methods (allows to save/load model weights)
        self.saver = tf.train.Saver()

        # Create or reuse session
        if sess is None:
            self.sess = tf.Session()
            self.sess.run(tf.global_variables_initializer())
        else:
            self.sess = sess

        # Load pretrained model
        if saver != "":
            self.saver.restore(self.sess, "saver/my_policy_net_pg.ckpt")

        # Stores training loss over time (useful for plotting)
        self.cost_his = []

    def _build_net(self, name):
        """
        This function builds:
        1. eval_net (used for learning)
        2. target_net (used for stable targets)
        3. loss (how wrong predictions are)
        4. optimizer (how to update weightss)
        """

        def build_layers(
            s, c_names, n_l1, w_initializer, b_initializer, trainable, name
        ):
            """
            Defines the neural network architecture
            Its called twice

            eval_net   (trainable=True)
            target_net (trainable=False)

            Parameters:
            s: Input tensor to the network (state)
                self.s      # current state  (for eval_net)
                self.s_     # next state     (for target_net)

            c_names: Collections (tell TensorFllow to store the variables in these collections)
                ¿Why its useful?
                Example:
                tf.get_collection("eval_net_params") retrieves all eval network weights

            n_l1: Number oof neurons in first hidden layer

            w_initializer: weight initialization (how weights are initialized)
                Example:
                w_initializer = tf.random_normal_initializer(0.0, 0.3)
                    mean = 0
                    std  = 0.3
            b_initializer: Bias initialization
                Example:
                b_initializer = tf.constant_initializer(0.1)

            trainable: Whether weights are updated
                True: For eval_net
                False: For target_net

            name: Scope prefix

            name and c_names are not redundant:
            Structure (name):
                eval_net/l1/w1
                eval_net/l2/w2

            Grouping (c_names):
                eval_net_params = [all eval weights]
            """

            """
            Creates first layer
                Creates a scope like:
                    eval_net_l1/
                    target_net_l1/
            """
            with tf.variable_scope(name + "l1"):
                # weights
                w1 = tf.get_variable(
                    "w1",
                    [self.n_features, n_l1],
                    initializer=w_initializer,
                    collections=c_names,
                    trainable=trainable,
                )
                # bias
                b1 = tf.get_variable(
                    "b1",
                    [1, n_l1],
                    initializer=b_initializer,
                    collections=c_names,
                    trainable=trainable,
                )
                # forward pass l1=ReLU(sW1​+b1​)
                l1 = tf.nn.relu(tf.matmul(s, w1) + b1)

            """
            Creates second layer
            """
            with tf.variable_scope(name + "l2"):
                # weights
                w2 = tf.get_variable(
                    "w2",
                    [150, 100],
                    initializer=w_initializer,
                    collections=c_names,
                    trainable=trainable,
                )
                # bias
                b2 = tf.get_variable(
                    "b2",
                    [1, 100],
                    initializer=b_initializer,
                    collections=c_names,
                    trainable=trainable,
                )
                # forward pass l2=ReLU(l1W2​+b2​)
                l2 = tf.nn.relu(tf.matmul(l1, w2) + b2)

            # Output layer (two cases)
            # First case Dueling DQN
            """
            Standard DQN
                network learns Q(s,a) directly
            Dueling DQN
                network learns:
                - how good state is (V)
                - which actions are better (A)
            """
            if self.dueling:

                # Value stream
                with tf.variable_scope(name + "Value"):
                    w3 = tf.get_variable(
                        "w3", [100, 1], initializer=w_initializer, collections=c_names
                    )
                    b3 = tf.get_variable(
                        "b3", [1, 1], initializer=b_initializer, collections=c_names
                    )
                    self.V = tf.matmul(l2, w3) + b3

                with tf.variable_scope(name + "Advantage"):
                    w2 = tf.get_variable(
                        "w2",
                        [100, self.n_actions],
                        initializer=w_initializer,
                        collections=c_names,
                    )
                    b2 = tf.get_variable(
                        "b2",
                        [1, self.n_actions],
                        initializer=b_initializer,
                        collections=c_names,
                    )
                    self.A = tf.matmul(l2, w2) + b2

                """
                Combine state value and advantages to get q values
                We substract the mean to enforce uniqueness in the V and A that get a particular Q
                See Theory/Dueling for more details
                """
                with tf.variable_scope(name + "Q"):
                    out = self.V + (
                        self.A - tf.reduce_mean(self.A, axis=1, keep_dims=True)
                    )

            # Standard DQN (directly outputs Q values)
            else:
                with tf.variable_scope(name + "Q"):
                    w2 = tf.get_variable(
                        "w2",
                        [100, self.n_actions],
                        initializer=w_initializer,
                        collections=c_names,
                    )
                    b2 = tf.get_variable(
                        "b2",
                        [1, self.n_actions],
                        initializer=b_initializer,
                        collections=c_names,
                    )

                    out = tf.matmul(l2, w2) + b2
            """
            Out: Is the output of the network
            out.shape = (batch_size, n_actions)
            out =
            [
                [1.2, 0.5, 2.1],   ← Q(s₁, a₁), Q(s₁, a₂), Q(s₁, a₃)
                [0.3, 1.8, 0.7]    ← Q(s₂, a₁), Q(s₂, a₂), Q(s₂, a₃)
            ]
            """
            return out

        """
        Inputs (placeholders)
        """

        """
        1. current state
            shape: (batch_size, n_features)
            None = flexible batch size
        """
        self.s = tf.placeholder(tf.float32, [None, self.n_features], name="s")
        """
        2. target Q-values
        """
        self.q_target = tf.placeholder(
            tf.float32, [None, self.n_actions], name=name + "Q_target"
        )

        """
        3. If PER
            Importance sampling weights (one per sample)
        """
        if self.prioritized:
            self.ISWeights = tf.placeholder(
                tf.float32, [None, 1], name=name + "IS_weights"
            )

        # Defines the Eval network (trainable)
        with tf.variable_scope(name + "eval_net"):

            c_names = ["eval_net_params", tf.GraphKeys.GLOBAL_VARIABLES]
            n_l1 = 150
            w_initializer = tf.random_normal_initializer(0.0, 0.3)
            b_initializer = tf.constant_initializer(0.1)

            self.q_eval = build_layers(
                self.s, c_names, n_l1, w_initializer, b_initializer, True, name
            )

        # Loss computation
        with tf.variable_scope(name + "loss"):

            # With PER
            if self.prioritized:
                # Per-sample TD error magnitude (used to update priorities)
                self.abs_errors = tf.reduce_sum(
                    tf.abs(self.q_target - self.q_eval), axis=1
                )
                # Weighted MSE
                self.loss = tf.reduce_mean(
                    self.ISWeights * tf.squared_difference(self.q_target, self.q_eval)
                )
            # Without PER
            else:
                # Standard MSE
                self.loss = tf.reduce_mean(
                    tf.squared_difference(self.q_target, self.q_eval)
                )

        """
        Training operation (how to update weights to reduce loss)
        Not executed yet, only defined
        """
        with tf.variable_scope(name + "train"):
            self._train_op = tf.train.RMSPropOptimizer(self.lr).minimize(self.loss)

        # Next state input
        self.s_ = tf.placeholder(tf.float32, [None, self.n_features], name="s_")

        # Defines the target network (not trainable)
        with tf.variable_scope(name + "target_net"):

            c_names = ["target_net_params", tf.GraphKeys.GLOBAL_VARIABLES]

            self.q_next = build_layers(
                self.s_, c_names, n_l1, w_initializer, b_initializer, False, name
            )

    def store_transition(self, sim_data):
        """
        One transition:
        s → current state
        a → action taken
        r → reward received
        s_ → next state
        """
        s = sim_data[0]
        a = sim_data[1]
        r = sim_data[2]
        s_ = sim_data[3]

        # Build a single vector
        transition = np.hstack((s, [a, r], s_))

        # Two cases
        """
        1. PER: 
            Transition stored with priority
        """
        if self.prioritized:
            self.memory.store(transition)

        # 2. Uniform Replay
        else:
            # Initialize counter
            if not hasattr(self, "memory_counter"):
                self.memory_counter = 0

            """
            Compute index (circular buffer)
            
            Example:
            counter = 0 → index = 0
            counter = 1 → index = 1
            ...
            counter = 4 → index = 4
            counter = 5 → index = 0  ← overwrite
            """
            index = self.memory_counter % self.memory_size
            # Store transition
            self.memory[index, :] = transition
            # Increment counter
            self.memory_counter += 1

    def choose_action(
        self, observation, n_actions, current_edge, conn_edges, e_distance
    ):
        """
        observation: State of the environment [travel times, number of vehicles, origin coords, destination coords]
        n_actions: Number available actions at current state
        current_edge: Edge where the vehicle is
        conn_edges: List of reachable edges from current edge
        e_distance: Euclidean distance of the edges to destination
        """

        """
        Prepare input
        Adds batch dimension

        Example:
        [0.2, 0.5, ...] → [[0.2, 0.5, ...]]
        Tensorflow expects: (batch_size, n_features)
        """
        observation = observation[np.newaxis, :]

        # Compute Q-values (forward pass through the network)
        actions_value = self.sess.run(self.q_eval, feed_dict={self.s: observation})

        # Epsilon greedy decision (explotation)
        if np.random.uniform() < self.epsilon:
            # Choose best action (action is an integer, the index of the chosen action)
            action = np.argmax(actions_value[0][:n_actions])
        # Exploration
        else:
            if n_actions > 1:
                # Smart exploration (60% of exploration uses guided strategy)
                if np.random.uniform() < 0.6:
                    # Container to store distances of outgoing edges to destination
                    prob_explore = []

                    for edge in conn_edges:
                        distance = e_distance[edge]
                        # Append euclidean distance to container
                        prob_explore.append(distance)

                    # Normalize
                    prob_explore = np.array(prob_explore)
                    prob_explore -= np.mean(prob_explore)
                    prob_explore /= np.std(prob_explore)
                    # Softmax (convert to probabilities)
                    prob_explore = self.softmax(prob_explore)

                    # Sample action (based on distance-based probabilities)
                    action = np.random.choice(range(n_actions), p=prob_explore)
                # Pure random exploration (40%)
                else:
                    action = np.random.randint(0, n_actions)
            # Edge case (only one possible move)
            else:
                action = 0

        # Return chosen action and q_values
        return action, actions_value

    def learn(self, episode, sim):
        """
        1. Sample past experiences
        2. Compute targets
        3. Compute losses
        4. Train the network
        5. Update priorities
        6. Update epsilon
        """
        # Update target network
        if self.learn_step_counter % self.replace_target_iter == 0:
            self.sess.run(self.replace_target_op)
            print("\ntarget_params_replaced\n")

        # Sample a batch
        # With PER
        if self.prioritized:
            tree_idx, batch_memory, ISWeights = self.memory.sample(self.batch_size)
        # Without PER
        else:
            sample_index = np.random.choice(self.memory_size, size=self.batch_size)
            batch_memory = self.memory[sample_index, :]

        """
        Compute Q-values for next states (for Double DQN)
        For next states (s') compute:
        q_next: from target_net
        q_eval4next: from eval_net
        """
        q_next, q_eval4next = self.sess.run(
            [self.q_next, self.q_eval],
            feed_dict={
                self.s_: batch_memory[:, -self.n_features :],
                self.s: batch_memory[:, -self.n_features :],
            },
        )

        """
        Compute Q-values for current states
        """
        q_eval = self.sess.run(
            self.q_eval, {self.s: batch_memory[:, : self.n_features]}
        )

        """
        Initialize targets (start with current predictions)
        We update the action that was actually taken (we leave the others unchanged)
        """
        q_target = q_eval.copy()

        # Extract components
        # a) Indices
        batch_index = np.arange(self.batch_size, dtype=np.int32)
        # b) Actions taken
        eval_act_index = batch_memory[:, self.n_features].astype(int)
        # c) Rewards r
        reward = batch_memory[:, self.n_features + 1]

        # Double DQN
        if self.double_q:
            # 1. Choose action using eval_net
            max_act4next = np.argmax(q_eval4next, axis=1)
            # 2. Evaluate it using target_net
            selected_q_next = q_next[batch_index, max_act4next]
        # Standard DQN (directly take max)
        else:
            selected_q_next = np.max(q_next, axis=1)
        # Bellman update
        q_target[batch_index, eval_act_index] = reward + self.gamma * selected_q_next

        # Train network
        """
        With PER
        - Update weights
        - Compute TD errors
        - Compute loss
        You compute the TD error during the training step, and then use that error 
        to update priorities after the gradient update step, but the error corresponds 
        to the pre-update prediction.
        """
        if self.prioritized:
            _, abs_errors, self.cost = self.sess.run(
                [self._train_op, self.abs_errors, self.loss],
                feed_dict={
                    self.s: batch_memory[:, : self.n_features],
                    self.q_target: q_target,
                    self.ISWeights: ISWeights,
                },
            )
            # Update priorities
            self.memory.batch_update(tree_idx, abs_errors)
        # Normal training
        else:
            _, self.cost = self.sess.run(
                [self._train_op, self.loss],
                feed_dict={
                    self.s: batch_memory[:, : self.n_features],
                    self.q_target: q_target,
                },
            )
        # Store loss
        self.cost_his.append(self.cost)

        # Update epsilon
        if self.epsilon < self.epsilon_max:
            self.epsilon += self.epsilon_increment
        else:
            self.epsilon = self.epsilon_max

        # Increment step counter
        self.learn_step_counter += 1

    def save(self):
        """
        Saves the model parameters (weights & biases)
        """
        self.saver.save(self.sess, "saver/my_policy_net_pg.ckpt")

    def softmax(self, x):
        """
        Converts scores to probabilities
        """
        x = x - np.max(x)
        exp_x = np.exp(x)
        return exp_x / np.sum(exp_x)
