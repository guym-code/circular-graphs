from loader import load_matrix, load_labels, load_secondary_labels
from edge_loader import load_edge_list_matrix_csv
from edge_list2mat import edge_list_to_matrix  

class CircularGraph:
    def __init__(self, mat_path, mat_type='matrix', labels=None, secondary_labels=None):

        if mat_type == 'edge_list':
            edge_index, edge_values = load_edge_list_matrix_csv(mat_path)
            self.mat = edge_list_to_matrix(edge_values, edge_index)

        elif mat_type == 'matrix':
            self.mat = self.load_matrix(mat_path)

        else:
            raise 

        self.labels = self.load_labels(labels)
        self.secondary_labels = self._load_secondary_labels(secondary_labels)

        self._validate()